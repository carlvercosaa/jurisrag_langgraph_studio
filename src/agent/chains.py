from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from agent import prompts
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini")

def generate_queries(query):
    multi_query_prompt = prompts.MULTI_QUERY_PROMPT

    multi_query_template = ChatPromptTemplate.from_template(multi_query_prompt)

    generate_queries_chain = multi_query_template | llm | StrOutputParser() | (lambda x: [q for q in x.split("\n") if q.strip()])

    questions = generate_queries_chain.invoke({"question": query})

    return questions

def retrieval_grader(query, doc):
    class GradeDocuments(BaseModel):
        """Binary score for relevance check on retrieved documents."""

        binary_score: str = Field(
            description="Documents are relevant to the question, 'yes' or 'no'"
        )

    structured_retriever_grader = llm.with_structured_output(GradeDocuments)

    retrieval_grader_system_prompt = prompts.RETRIEVAL_GRADER_SYSTEM_PROMPT
        
    grade_template = ChatPromptTemplate.from_messages(
        [
            ("system", retrieval_grader_system_prompt),
            ("human", "User question: {question} \n\n Retrieved document: \n\n {document}"),
        ]
    )

    retrieval_grader_chain = grade_template | structured_retriever_grader

    grade = retrieval_grader_chain.invoke({"question": query, "document": doc})

    return grade

def answer_question(question, context):
    generate_answer_prompt = prompts.GENERATE_ANSWER_PROMPT

    generate_answer_template = ChatPromptTemplate.from_template(generate_answer_prompt)

    answer_question_chain = generate_answer_template | llm | StrOutputParser()

    answer = answer_question_chain.invoke({"question": question, "context": context})

    return answer

def hallucinations_grader(documents, generation):
    class GradeHallucinations(BaseModel):
        """Binary score for hallucination present in generation answer."""

        binary_score: str = Field(
            description="Answer is grounded in the facts, 'yes' or 'no'"
        )

    structured_llm_grader = llm.with_structured_output(GradeHallucinations)

    hallucination_grader_system_prompt = prompts.HALLUCINATIONS_GRADER_SYSTEM_PROMPT

    hallucination_template = ChatPromptTemplate.from_messages(
        [
            ("system", hallucination_grader_system_prompt),
            ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
        ]
    )

    hallucinations_grader_chain = hallucination_template | structured_llm_grader

    hallucination = hallucinations_grader_chain.invoke({"documents": documents, "generation": generation})

    return hallucination

def final_rag_answer(qr_text, original_question):
    final_answer_prompt = prompts.FINAL_ANSWER_PROMT

    final_answer_template = ChatPromptTemplate.from_template(final_answer_prompt)

    final_rag_answer_chain = final_answer_template | llm | StrOutputParser()

    answer = final_rag_answer_chain.invoke({"qr_text": qr_text, "original_question": original_question})

    return answer

def answer_grader(question, generation):
    class GradeAnswer(BaseModel):
        """Binary score to assess answer addresses question."""

        binary_score: str = Field(
            description="Answer addresses the question, 'yes' or 'no'"
        )

    structured_answer_grader = llm.with_structured_output(GradeAnswer)

    answer_grader_system_prompt = prompts.ANSWER_GRADER_SYSTEM_PROMPT

    answer_template = ChatPromptTemplate.from_messages(
        [
            ("system", answer_grader_system_prompt),
            ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
        ]
    )

    answer_grader_chain = answer_template | structured_answer_grader

    grade = answer_grader_chain.invoke({"question": question, "generation": generation})

    return grade

def question_rewriter(question, documents):
    question_rewriter_system_prompt = prompts.QUESTION_REWRITER_SYSTEM_PROMPT
        
    question_rewriter_template = ChatPromptTemplate.from_messages(
        [
            ("system", question_rewriter_system_prompt),
            (
                "human","""Here is the initial question: \n\n {question} \n,
                Here is the document: \n\n {documents} \n ,
                Formulate an improved question. if possible other return 'question not relevant'."""
            ),
        ]
    )

    question_rewriter_chain = question_rewriter_template | llm | StrOutputParser()

    question_rewriter_chain.invoke({"question": question, "documents": documents})
