import os
import hashlib
from pypdf import PdfReader
from logger import logger

# Pasta para PDF de conhecimento
KNOWLEDGE_DIR = "knowledge_base"
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

def ingest_pdf(file_path):
    """
    Versão leve: Lê o PDF e loga o sucesso. 
    Removido Langchain e ChromaDB para caber nos 512MB do Render Free.
    """
    try:
        reader = PdfReader(file_path)
        file_name = os.path.basename(file_path)
        
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t
            
        logger.info(f"PDF '{file_name}' lido com sucesso ({len(text)} caracteres).")
        return {"file": file_name, "status": "read"}
    except Exception as e:
        logger.error(f"Erro ao ler PDF: {e}")
        return {"error": str(e)}

def process_new_pdfs():
    pass
