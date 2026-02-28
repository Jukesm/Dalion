import os
import hashlib
from pypdf import PdfReader
from vector_memory import collection, client
from logger import logger
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Pasta para PDF de conhecimento
KNOWLEDGE_DIR = "knowledge_base"
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

def get_content_hash(content):
    """Gera um hash MD5 para o conteúdo de um chunk."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def ingest_pdf(file_path):
    """Lê um PDF, quebra em pedaços e salva na memória vetorial com deduplicação."""
    try:
        reader = PdfReader(file_path)
        file_name = os.path.basename(file_path)
        logger.info(f"Iniciando ingestão de PDF (Hardened): {file_name}")
        
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        # Chunking Semântico
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " "]
        )
        chunks = text_splitter.split_text(full_text)
            
        added_count = 0
        for i, chunk in enumerate(chunks):
            chunk_hash = get_content_hash(chunk)
            chunk_id = f"doc_{chunk_hash}" # ID baseado no hash para deduplicação automática
            
            # O ChromaDB com .add() em IDs existentes apenas sobrescreve (deduplicação)
            collection.add(
                documents=[chunk],
                metadatas=[{"source": file_name, "chunk": i, "hash": chunk_hash}],
                ids=[chunk_id]
            )
            added_count += 1
        
        logger.info(f"Sucesso: {added_count} trechos processados (MD5 Deduplicated) de '{file_name}'.")
        return {"file": file_name, "chunks": added_count}
    except Exception as e:
        logger.error(f"Erro ao processar PDF {file_path}: {e}")
        return {"error": str(e)}

def process_new_pdfs():
    """Varre a pasta knowledge_base por novos PDFs."""
    files = [f for f in os.listdir(KNOWLEDGE_DIR) if f.endswith(".pdf")]
    for file in files:
        path = os.path.join(KNOWLEDGE_DIR, file)
        # Por simplicidade, re-ingere se estiver lá, ou remove após processar (ajustável)
        ingest_pdf(path)
        # Opcional: mover para uma pasta 'processed'
        # os.rename(path, os.path.join(KNOWLEDGE_DIR, "processed", file))
