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
    Retrieve relevant FAQ answers based on a user query.

    Use this tool when the user asks a general question, support topics, or common issues.

    Parameters:
        query (str): The user's question or issue in natural language.

    Returns:
        str: A formatted string containing the top 2 most relevant FAQ question-answer pairs.

    Notes:
        - Best used for general support questions, not product-specific queries.
        - Prefer other tools if the query is about a specific product, order, or inventory.
    """

    answer = faqs.similarity_search(query=query, k=2)
    return format_faq(answer)