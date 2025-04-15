from databricks.vector_search.client import VectorSearchClient
from langchain_community.vectorstores import DatabricksVectorSearch
from typing import List
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph, START
from agent import chains
import os
from dotenv import load_dotenv

load_dotenv()

databricks_host = os.environ.get("DATABRICKS_HOST")
databricks_token = os.environ.get("DATABRICKS_TOKEN")
endpoint_name = os.environ.get("ENDPOINT_NAME")
index_name = os.environ.get("INDEX_NAME")
embeddings_endpoint = os.environ.get("EMBEDDINGS_ENDPOINT")

vs_client = VectorSearchClient(disable_notice=True)

index = vs_client.get_index(endpoint_name=endpoint_name, index_name=index_name)

text_column = 'Conteudo'
        
columns = ["Conteudo", "Indice"]
        
search_kwargs = {"k": 4}
        
vector_search = DatabricksVectorSearch(
    index,
    text_column= text_column,
    columns = columns,
)
        
retriever = vector_search.as_retriever(search_kwargs=search_kwargs)

class AgentState(TypedDict):
    original_question: str
    questions: List[str]
    reasonings: List[str]
    documents: List[str]
    final_reasoning: str
    filter_documents: List[str]
    unfilter_documents: List[str]

def decompose_question(state:AgentState):
    print("----DECOMPOSING QUESTION----")

    question = state["original_question"]

    questions = chains.generate_queries(question)

    print("""----QUESTIONS----""")
    for q in questions:
        print(q)

    return {"questions": questions}

def retrieve(state:AgentState):
    print("----RETRIEVING DOCUMENTS----")

    questions=state['questions']

    documents = []

    for q in questions:
        documents.append(retriever.invoke(q))

    page_contents = []

    for docx_index, docx in enumerate(documents):
        page_contents.append([])
        for docy in docx:
            if not any(docy.page_content in sublist for sublist in page_contents):
                page_contents[docx_index].append(docy.page_content)
    print("----DOCUMENTS RETRIEVED----")

    return {"documents": page_contents, "questions": questions}

def grade_documents(state:AgentState):
    print("----CHECKING DOCUMENTS RELEVANCE TO EACH QUESTION----")

    questions = state['questions']
    documents = state['documents']
    
    filtered_docs = []
    unfiltered_docs = []

    for docx_index, (q, docx) in enumerate(zip(questions, documents)):
        filtered_docs.append([])
        unfiltered_docs.append([])
        print("----CURRENT QUESTION----")
        print(q)
        for docy in docx:
            score = chains.retrieval_grader(q, docy)
            grade = score.binary_score
                
            if grade=='yes':
                print("----GRADE: DOCUMENT RELEVANT----")
                print("----DOCUMENT----")
                print(docy)
                filtered_docs[docx_index].append(docy)
            else:
                print("----GRADE: DOCUMENT NOT RELEVANT----")
                print("----DOCUMENT----")
                print(docy)
                unfiltered_docs[docx_index].append(docy)

    empty_list = [i for i, sublista in enumerate(filtered_docs) if not sublista]

    refiltered_docs = [sublista for i, sublista in enumerate(filtered_docs) if i not in empty_list]
    refiltered_questions = [item for i, item in enumerate(questions) if i not in empty_list]

    if len(unfiltered_docs)>4:
        return {"unfilter_documents": unfiltered_docs,"filter_documents":[], "questions": questions}
    else:
        return {"filter_documents": refiltered_docs,"unfilter_documents":[],"questions": refiltered_questions}

def decide_to_generate(state:AgentState):
    print("----DECIDE TO GENERATE----")

    state["questions"]
    
    unfiltered_documents = state["unfilter_documents"]
    filtered_documents = state["filter_documents"]
    
    if filtered_documents:
        print("----DECISION: GENERATE----")
        return "generate"
    if unfiltered_documents:
        print("----ALL THE DOCUMENTS ARE NOT RELEVANT TO QUESTIONS, TRANSFORM QUERY----")
        return "transform_query"

def generate(state:AgentState):
    print("----GENERATEING RESPONSE----")
    
    questions=state["questions"]
    documents=state["filter_documents"]

    reasonings = []

    for q, doc in zip(questions, documents):
        if len(doc) > 0:
            current_reasoning = chains.answer_question(doc, q)
            print(f"REASONING:{current_reasoning}")
            reasonings.append(current_reasoning)

    return {"documents":documents,"questions":questions,"reasonings":reasonings}

def transform_query(state:AgentState):
    print("----TRANSFORMING QUERY----")

    question=state["original_question"]
    documents=state["documents"]

    response = chains.question_rewriter(question, documents)

    print(f"----RESPONSE----")
    print(response)
    
    if response == 'question not relevant':
        print("----QUESTION IS NOT AT ALL RELEVANT----")
        return {"documents":documents,"question":response,"generation":"question was not at all relevant"}
    else:   
        return {"documents":documents,"question":response}

def decide_to_generate_after_transformation(state:AgentState):
    question=state["question"]
    
    if question=="question not relevant":
        return "query_not_at_all_relevant"
    else:
        return "Retriever"

def grade_generation_vs_documents_and_question(state:AgentState):
    print("---CHECKING HALLUCINATIONS---")
    
    questions= state['questions']
    documents = state['filter_documents']
    reasonings = state["reasonings"]

    filtered_reasonings = []

    for question, reasoning in zip(questions, reasonings):
            print("---GRADE REASONING VS QUESTION ---")
            print(reasoning)
            score = chains.answer_grader(question, reasoning)
            grade = score.binary_score
            if grade=='yes':
                print("---DECISION: GENERATION ADDRESS THE QUESTION ---")
                filtered_reasonings.append(reasoning)
            else:
                print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---TRANSFORM QUERY")
    
    return {"reasonings": filtered_reasonings}

def hallucination_router(state:AgentState):

  print("----CHECKING HALLUCINATION ROUTING----")
  reasonings = state["reasonings"]

  if reasonings:
    print("----DECISION: NO HALLUCINATION---")
    return "usefulco"
  else:
    print("----DECISION: HALLUCINATION---")
    return "not useful"
  
def final_answer(state:AgentState):
    print("---GENERATING FINAL ANSWER ---")

    question = state["original_question"]
    reasonings = state["reasonings"]

    final_reasoning = chains.final_rag_answer(question, reasonings)

    print(final_reasoning)

    return {"final_reasoning": final_reasoning}

def final_hallucination(state:AgentState):
  print("----CHECKING HALLUCINATION----")

  final_reasoning = state["final_reasoning"]
  question = state["original_question"]

  score = chains.answer_grader(question, final_reasoning)
  grade = score.binary_score

  if grade=='yes':
    print("----DECISION: NO HALLUCINATION---")
    return "useful"
  else:
    print("----DECISION: HALLUCINATION---")
    return "not useful"
  
workflow = StateGraph(AgentState)

workflow.add_node("Multi_Query_Generator", decompose_question)

workflow.add_node("Docs_Vector_Retrieve", retrieve)

workflow.add_node("Grading_Generated_Documents", grade_documents)

workflow.add_node("Content_Generator", generate)

workflow.add_node("Transform_User_Query", transform_query)

workflow.add_node("Grade_Reasoning_VS_Question", grade_generation_vs_documents_and_question)

workflow.add_node("Final_Content_Generator", final_answer)

workflow.add_edge(START,"Multi_Query_Generator")

workflow.add_edge("Multi_Query_Generator","Docs_Vector_Retrieve")

workflow.add_edge("Docs_Vector_Retrieve","Grading_Generated_Documents")

workflow.add_conditional_edges("Grading_Generated_Documents",
                            decide_to_generate,
                            {
                            "generate": "Content_Generator",
                            "transform_query": "Transform_User_Query"
                            }
                            )

workflow.add_edge("Content_Generator", "Grade_Reasoning_VS_Question")

workflow.add_conditional_edges("Grade_Reasoning_VS_Question",
                            hallucination_router,
                            {
                            "usefulco": "Final_Content_Generator",
                            "not useful": "Transform_User_Query"
                            }
                            )

workflow.add_conditional_edges("Transform_User_Query",
                            decide_to_generate_after_transformation,
                            {
                            "Retriever":"Multi_Query_Generator",
                            "query_not_at_all_relevant":END
                            }
                            )

workflow.add_conditional_edges("Final_Content_Generator",
                            final_hallucination,
                            {
                            "useful":END,
                            "not useful": "Transform_User_Query",
                            }
                            )

graph=workflow.compile()

graph.name = "New Graph"  # This defines the custom name in LangSmith
