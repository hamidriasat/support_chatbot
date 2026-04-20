from database.chroma_config import faqs
from langchain.tools import tool


def format_faq(docs: list):

    formatted_context = "\n\n".join([
    f"Document {i+1}:\n{doc.page_content}" 
    for i, doc in enumerate(docs)
    ])

    return formatted_context


@tool(description="faq_tool")
def faq_tool(query:str):
    """
    takes the user query return the relevent faq question and answer
    """

    answer = faqs.similarity_search(query=query, k=2)
    return format_faq(answer)