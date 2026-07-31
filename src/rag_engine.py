import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

DB_PATH = "data/vectorstore"

PROMPT_TEMPLATE = """
Você é um auditor especialista em análise de contratos corporativos.
Sua missão é responder à pergunta do usuário baseando-se EXCLUSIVAMENTE nos trechos de contrato fornecidos no Contexto abaixo.

REGRAS DE COMPLIANCE ESTREITAS:
1. Se a resposta não estiver explicitamente mencionada no Contexto abaixo, responda EXATAMENTE: "Informação não encontrada na documentação fornecida." Não invente ou presuma nada.
2. Para cada afirmação ou dado citado na sua resposta, você DEVE apontar a fonte no final da frase no seguinte formato: [Fonte: NOME_DO_ARQUIVO | Pág: X].
3. Seja direto, analítico e imparcial.

Contexto Recuperado do Banco Vetorial:
{context}

---
Pergunta do Usuário: {question}

Resposta Analítica com Citação de Fontes:
"""

def get_retriever():
    """Conecta-se ao ChromaDB local e retorna o retriever configurado."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings
    )
    return vectorstore.as_retriever(search_kwargs={"k": 3})

def query_contract_copilot(user_query: str) -> dict:
    """
    Executa a busca vetorial no ChromaDB e gera uma resposta fundamentada
    com citação de fontes utilizando o LLM da Groq.
    """
    retriever = get_retriever()
    retrieved_docs = retriever.invoke(user_query)
    
    context_parts = []
    for doc in retrieved_docs:
        source_file = os.path.basename(doc.metadata.get("source", "contrato_desconhecido.pdf"))
        page_num = doc.metadata.get("page", 0) + 1 
        context_parts.append(f"[Arquivo: {source_file} | Pág: {page_num}]\n{doc.page_content}")
        
    formatted_context = "\n\n---\n\n".join(context_parts)
    
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    chain = prompt_template | llm | StrOutputParser()
    
    answer = chain.invoke({
        "context": formatted_context,
        "question": user_query
    })
    
    return {
        "pergunta": user_query,
        "resposta": answer,
        "documentos_consultados": list(set(os.path.basename(doc.metadata.get("source", "")) for doc in retrieved_docs)),
        "contexto_bruto": [doc.page_content for doc in retrieved_docs]
    }