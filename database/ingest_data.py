import pandas as pd
import json
from langchain_core.documents import Document
from langchain_community.document_loaders import DataFrameLoader
from langchain_chroma import Chroma
from database.chroma_config import CHROMA_PATH, initialize_embedding
from utils.config import settings


def chroma_embedd(document, embedding, collection):
    print(f"Embedding {len(document)} records into '{collection}'...")

    Chroma.from_documents(
        documents=document,
        embedding=embedding,
        persist_directory=CHROMA_PATH,
        collection_name=collection
    )

    print(f"Ingestion complete for '{collection}'.")


def build_catalog(page_content_column, collection_name):
    df = pd.read_csv(settings.get("PRODUCT_DATA_PATH"))
    df = df.fillna("information not available")

    embeddings = initialize_embedding()

    loader = DataFrameLoader(df, page_content_column=page_content_column)
    documents = loader.load()
    chroma_embedd(document=documents, embedding=embeddings, collection=collection_name)


def faq_catalog(collection_name):
    path = settings.get("FAQ_DATA_PATH")
    if not path or "" == path:
        print("Put faq json path in your setting file with name FAQ_DATA_PATH.")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    # Convert to LangChain Documents
    documents = []
    for item in data:
        content = f"Question: {item['question']}\nAnswer: {item['answer']}"
        doc = Document(page_content=content, metadata={"source": "faqs_json"})
        documents.append(doc)
    
    embeddings = initialize_embedding()
    chroma_embedd(document=documents, embedding=embeddings, collection=collection_name)



if __name__ == "__main__":
    build_catalog("description", "products_desc")
    build_catalog("product_name", "products_name")
    faq_catalog("faqs")