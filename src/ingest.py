import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Carrega as variáveis de ambiente
load_dotenv()

# Caminhos das pastas (relativos à raiz do projeto)
DATA_PATH = "data/raw_contracts"
DB_PATH = "data/vectorstore"

def executar_ingestao():
    """Lê PDFs da pasta, divide em chunks e salva no banco vetorial ChromaDB."""
    print("Iniciando a leitura dos PDFs...")
    loader = PyPDFDirectoryLoader(DATA_PATH)
    docs = loader.load()
    
    if not docs:
        print("Nenhum documento encontrado na pasta.")
        return

    print(f"Total de páginas carregadas: {len(docs)}")

    # Estratégia de Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Os documentos foram divididos em {len(chunks)} blocos (chunks).")

    # Embeddings locais (Open Source)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Gerando embeddings e salvando no banco vetorial...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    print(f"Vetorização concluída com sucesso! Banco salvo em: {DB_PATH}")

if __name__ == "__main__":
    executar_ingestao()