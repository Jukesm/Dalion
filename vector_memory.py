import chromadb
from chromadb.utils import embedding_functions

# Configuração do banco vetorial persistente
client = chromadb.PersistentClient(path="./chroma_db")

# Usando um modelo de embeddings leve e eficiente
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")

# Criação ou obtenção da coleção de ideias
collection = client.get_or_create_collection(
    name="ideas_memory",
    embedding_function=embedding_func
)

def add_idea_to_memory(idea_id, title, description, target_audience):
    """Armazena uma ideia no banco vetorial para busca semântica futura."""
    content = f"Título: {title}. Descrição: {description}. Público: {target_audience}"
    
    collection.add(
        documents=[content],
        metadatas=[{"title": title, "id": idea_id}],
        ids=[str(idea_id)]
    )
    print(f"Ideia {idea_id} adicionada à memória vetorial.")

def search_similar_ideas(query_text, n_results=3):
    """Busca ideias semanticamente similares na memória."""
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results
