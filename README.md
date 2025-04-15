## 📑 Visão Geral
JurisRAG é um sistema avançado de Retrieval-Augmented Generation (RAG) com auto-reflexão, especificamente adaptado para o domínio jurídico. Utilizando uma arquitetura multi-agentes, o sistema decompõe questões jurídicas complexas, recupera documentos relevantes, avalia a qualidade das informações recuperadas e gera respostas precisas com verificação de alucinações.

## 🔍 Arquitetura
O sistema implementa um fluxo de trabalho especializado que inclui:

- Multi_Query_Generator: Decompõe questões jurídicas complexas em múltiplas sub-consultas para otimizar a recuperação de informações relevantes.
- Docs_Vector_Retrieve: Recupera documentos jurídicos relevantes a partir de uma base de conhecimento vetorizada.
- Grading_Generated_Documents: Avalia a qualidade e relevância dos documentos recuperados em relação às consultas originais.
- Content_Generator: Gera conteúdo inicial com base nos documentos aprovados.
- Grade_Reasoning_VS_Question: Avalia se o raciocínio jurídico aplicado é adequado para a questão original.
- Final_Content_Generator: Refina o conteúdo para produzir a resposta final.
- Transform_User_Query: Reformula ou redireciona a consulta quando necessário.

## ⚙️ Tecnologias Utilizadas
- Python
- LangGraph
- LangGraph Studio
- LangChain
- Databricks Vectorsearch
- OpenAI API

## 🌟 Características principais

Decomposição Inteligente de Questões: Divide perguntas jurídicas complexas em componentes mais simples para melhorar a precisão da recuperação.
Avaliação de Qualidade de Documentos: Filtra documentos jurídicos recuperados com base na relevância para a consulta específica.
Verificação de Alucinações: Implementa mecanismos para detectar e corrigir informações incorretas ou fabricadas nas respostas geradas.
Fluxo de Trabalho Adaptativo: Redireciona consultas ou refina respostas conforme necessário ao longo do processo.

## 📋 Fluxo de Processamento

1 - O usuário submete uma questão jurídica.
2 - O sistema decompõe a questão em múltiplas consultas específicas.
3 - Documentos jurídicos são recuperados para cada consulta.
4 - A qualidade dos documentos é avaliada.
5 - Uma resposta inicial é gerada para cada pergunta decomposta com base nos documentos aprovados.
6 - Os raciocínios jurídicos são avaliados.
7 - Se o raciocínio for útil, uma resposta final é gerada com base nos raciocínios aprovados.
8 - Caso contrário, a consulta é transformada ou redirecionada.

## 📈 Avaliação de Desempenho
O sistema inclui métricas para avaliar o desempenho:

Precisão das Respostas: Comparação com respostas de referência.
Relevância dos Documentos: Taxa de documentos relevantes recuperados.
Detecção de Alucinações: Porcentagem de alucinações corretamente identificadas.
Tempo de Processamento: Latência total e por componente.

## 🚀 Como Usar

1 - Clone este repositório.
2 - Crie e ative um ambiente virtual: python -m venv venv
source venv/bin/activate
3 - Instale as dependências: pip install -e .
pip install --upgrade "langgraph-cli[inmem]"
4 - Configure as variáveis de ambiente.
5 - Launch LangGraph Server: langgraph dev