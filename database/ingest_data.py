import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_chroma import Chroma
from database.chroma_config import CHROMA_PATH, initialize_embedding
from utils.config import settings


def build_catalog(page_content_column, collection_name):
    df = pd.read_csv(settings.get("PRODUCT_DATA_PATH"))
    df = df.fillna("information not available")

    embeddings = initialize_embedding()

    loader = DataFrameLoader(df, page_content_column=page_content_column)
    documents = loader.load()

    print(f"Embedding {len(documents)} records into '{collection_name}'...")

    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
        collection_name=collection_name
    )

    print(f"Ingestion complete for '{collection_name}'.")

if __name__ == "__main__":
    build_catalog("description", "products_desc")
    build_catalog("product_name", "products_name")