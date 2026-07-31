import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

from business_rules import audit_contract_compliance

# 1. Carregamento obrigatório de variáveis de ambiente (.env)
load_dotenv()

# =====================================================================
# CONFIGURAÇÃO GERAL DA PÁGINA (DESIGN SÓBRIO / SEM EMOJIS)
# =====================================================================
st.set_page_config(
    page_title="Copiloto de Auditoria Contratual e RAG",
    layout="wide"
)

st.title("Copiloto de Análise Contratual e Compliance RAG")
st.caption("Sistema analítico para triagem de contratos via linguagem natural e auditoria determinística de conformidade.")

# Inicialização de variáveis de controle no estado da sessão
if "retriever_ativo" not in st.session_state:
    st.session_state.retriever_ativo = None
if "nome_arquivo_ativo" not in st.session_state:
    st.session_state.nome_arquivo_ativo = None

# =====================================================================
# BARRA LATERAL: INGESTÃO DINÂMICA EM MEMÓRIA (ISOLAMENTO DE FONTE)
# =====================================================================
st.sidebar.header("Painel de Controle")
st.sidebar.subheader("Analisar Novo Contrato")
st.sidebar.caption("O PDF carregado abaixo será o único documento indexado para consulta na sessão atual.")

arquivo_pdf = st.sidebar.file_uploader("Selecione um contrato PDF", type=["pdf"])

if arquivo_pdf is not None:
    caminho_dir = "data/raw_contracts"
    os.makedirs(caminho_dir, exist_ok=True)
    caminho_temp = os.path.join(caminho_dir, arquivo_pdf.name)
    
    with open(caminho_temp, "wb") as f:
        f.write(arquivo_pdf.getbuffer())
    
    with st.sidebar.status("Indexando contrato na memória temporária..."):
        loader = PyPDFLoader(caminho_temp)
        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)
        
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Instanciação temporária e isolada (in-memory) do ChromaDB
        vectorstore_dinamico = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings
        )
        
        st.session_state.retriever_ativo = vectorstore_dinamico.as_retriever(search_kwargs={"k": 3})
        st.session_state.nome_arquivo_ativo = arquivo_pdf.name
        
    st.sidebar.success(f"Contrato '{arquivo_pdf.name}' pronto para consulta exclusiva.")

if st.session_state.nome_arquivo_ativo:
    st.sidebar.info(f"Documento em Análise:\n{st.session_state.nome_arquivo_ativo}")
else:
    st.sidebar.warning("Nenhum contrato carregado. Envie um arquivo PDF para habilitar o módulo RAG.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Regras de Negócio Ativas:")
st.sidebar.markdown("- REGRA-MULTA-001: Alerta para multas superiores a 10%.")
st.sidebar.markdown("- REGRA-REAJUSTE-001: Exige citação de índice oficial (IPCA, IGP-M, etc.).")

# =====================================================================
# MOTOR RAG COM RASTREABILIDADE DE FONTES
# =====================================================================
def consultar_contrato_isolado(user_query: str, retriever):
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
    retrieved_docs = retriever.invoke(user_query)
    
    context_parts = []
    for doc in retrieved_docs:
        source_file = os.path.basename(doc.metadata.get("source", "contrato.pdf"))
        page_num = doc.metadata.get("page", 0) + 1 
        context_parts.append(f"[Arquivo: {source_file} | Pág: {page_num}]\n{doc.page_content}")
        
    formatted_context = "\n\n---\n\n".join(context_parts)
    
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    chain = prompt_template | llm | StrOutputParser()
    answer = chain.invoke({"context": formatted_context, "question": user_query})
    
    return {
        "pergunta": user_query,
        "resposta": answer,
        "documentos_consultados": list(set(os.path.basename(doc.metadata.get("source", "")) for doc in retrieved_docs))
    }

# =====================================================================
# ABAS DE NAVEGAÇÃO DA INTERFACE
# =====================================================================
tab_rag, tab_rules = st.tabs(["Consultar Contratos (RAG)", "Auditoria Rápida de Cláusula"])

with tab_rag:
    st.subheader("Consulta em Linguagem Natural com Citação de Origem")
    
    user_query = st.text_input(
        "Digite sua pergunta ou instrução analítica:",
        placeholder="Ex: Qual é a porcentagem da multa rescisória e o índice de reajuste contratual?"
    )
    
    if st.button("Executar Consulta RAG", type="primary"):
        if not st.session_state.retriever_ativo:
            st.error("Erro: Envie um arquivo PDF no painel lateral antes de executar uma consulta.")
        elif user_query.strip():
            with st.spinner("Consultando vetores e validando informações com o LLM..."):
                try:
                    resultado = consultar_contrato_isolado(user_query, st.session_state.retriever_ativo)
                    st.markdown("### Resposta Analítica")
                    st.success(resultado["resposta"])
                    
                    with st.expander("Detalhes de Rastreabilidade e Fontes Consultadas"):
                        for fonte in resultado["documentos_consultados"]:
                            st.write(f"- Arquivo mapeado: {fonte}")
                except Exception as e:
                    st.error(f"Falha de execução RAG: {str(e)}")
        else:
            st.warning("Aviso: Digite uma pergunta válida antes de consultar.")

with tab_rules:
    st.subheader("Validação de Cláusula em Código Nativo (RegEx / Python)")
    st.markdown("Cole um trecho contratual abaixo para verificar desvios de compliance de forma determinística:")
    
    texto_clausula = st.text_area(
        "Trecho Contratual para Auditoria:",
        height=150,
        placeholder="Ex: Em caso de rescisão incidirá multa de 15%. O reajuste será negociado anualmente."
    )
    
    if st.button("Auditar Cláusula", key="btn_audit"):
        if texto_clausula.strip():
            audit_res = audit_contract_compliance(texto_clausula)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status - Multa Rescisória", audit_res["status_multa"])
            with col2:
                st.metric("Status - Índice de Reajuste", audit_res["status_reajuste"])
                
            st.markdown("### Alertas de Compliance:")
            if audit_res["alertas"]:
                for alerta in audit_res["alertas"]:
                    st.error(alerta)
            else:
                st.success("Nenhum desvio de compliance identificado. Cláusula em conformidade.")
        else:
            st.warning("Aviso: Insira um texto contratual para auditar.")