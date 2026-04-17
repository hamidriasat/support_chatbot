import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_chroma import Chroma
from database.chroma_config import CHROMA_PATH, initialize_embedding
from utils.config import settings

def build_catalog():
    df = pd.read_csv(settings.get("PRODUCT_DATA_PATH"))
    df = df.fillna("information not available")
    embeddings = initialize_embedding()
    # Initialize Loader (Embedding ONLY the 'name' or 'description' column)
    loader = DataFrameLoader(df, page_content_column="description")
    documents = loader.load()
    
    print(f"Embedding {len(documents)} records into Chroma...")
    
    # This creates the physical files in your ./chroma_db folder
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
        collection_name="products_desc" # Matches your config name
    )
    print("Ingestion complete.")

if __name__ == "__main__":
    build_catalog()