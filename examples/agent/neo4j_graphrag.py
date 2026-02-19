"""
`neo4j-graphrag`示例
"""

from neo4j import GraphDatabase
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings import OpenAIEmbeddings

from src.thera.config import settings

# Connect to Neo4j database
driver = GraphDatabase.driver(
    settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
)

# Creating the index
create_vector_index(
    driver,
    settings.neo4j_index_name,
    label="Document",
    embedding_property="vectorProperty",
    dimensions=1536,
    similarity_fn="euclidean",
)

# Create Embedder object, needed to convert the user question (text) to a vector
embedder = OpenAIEmbeddings(model=settings.llm_embedding_model)

# Initialize the retriever
retriever = VectorRetriever(driver, settings.neo4j_index_name, embedder)

# Initialize the LLM
# Note: the `LLM_API_KEY`` must be in the env vars
llm = OpenAILLM(model_name=settings.llm_model, model_params={"temperature": 0})

# Initialize the RAG pipeline
rag = GraphRAG(retriever=retriever, llm=llm)

# Query the graph
query_text = "How do I do similarity search in Neo4j?"
response = rag.search(query_text=query_text, retriever_config={"top_k": 5})
print(response.answer)
