import os
import logging
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from utils.config import settings
from utils.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)
# Define paths
CHROMA_PATH = os.path.join(os.getcwd(), "chroma_db")
EMBEDDING = None

def initialize_embedding():

    openai_api_key = settings.get("OPENAI_API_KEY")
    embedd_model = settings.get("EMBEDDING_MODEL")

    if not openai_api_key or openai_api_key == "":
        logger.error("Configuration error: Check OPENAI_API_KEY")
        raise ValueError("OPENAI_API_KEY is missing for embedding.")
    
    if not embedd_model:
        logger.error("Configuration error: Embedding model name is missing")
        raise ValueError("Missing configuration: Embedding model name is not set.")
    
    embeddings = OpenAIEmbeddings(model=embedd_model, api_key=openai_api_key)
    return embeddings


def get_vector_store(collection_name: str):
    """
    Returns a connection to a specific collection. 
    Chroma handles the 'create if not exists' logic automatically 
    when you point it to the persist_directory.
    """
    global EMBEDDING
    if not EMBEDDING:
        EMBEDDING = initialize_embedding()
    return Chroma(
        collection_name=collection_name,
        persist_directory=CHROMA_PATH,
        embedding_function=EMBEDDING
    )

# Pre-initialize instances for easy import
product_name = get_vector_store("products_name")
product_desc = get_vector_store("products_desc")
faqs = get_vector_store("faqs")