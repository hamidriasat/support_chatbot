import pandas as pd
from langchain.tools import tool
from database.chroma_config import product_name, product_desc
from utils.config import settings

DF = pd.read_csv(settings.get("PRODUCT_DATA_PATH"))
DF.set_index('product_id', inplace=True)

# 2. Convert others to 'category' for fast filtering
for col in ['category', 'sub_category', 'brand']:
    DF[col] = DF[col].astype('category')


def _format_product(product):
    """Format a single product row as a concise string"""
    # product is a pandas Series with the product_id as the index
    try:
        product_id = product.name
        product_name = product.get('product_name', 'N/A')
        description = product.get('description', 'N/A')
        brand = product.get('brand', 'N/A')
        category = product.get('category', 'N/A')
        sub_category = product.get('sub_category', 'N/A')
        imported_from = product.get('Imported_from', 'N/A')
        
        return f"ID: {product_id}, Name: {product_name}, Description: {description}, Brand: {brand}, Category: {category}, Sub-Category: {sub_category}, Imported from: {imported_from}"
    except Exception as e:
        return f"Error formatting product: {str(e)}"


def _format_products(products_df, limit=3):
    """Format multiple products as a concise string, limited to top N results"""
    if products_df.empty:
        return "No products found."
    
    results = []
    for idx, (product_id, product) in enumerate(products_df.iterrows()):
        if idx >= limit:
            remaining = len(products_df) - limit
            results.append(f"\n... and {remaining} more products")
            break
        results.append(_format_product(product))
    
    return "\n".join(results)


#tool for search product by id
@tool("product_search_id")
def product_search_id(id:str):
    """
    Retrieve product details using an exact product ID.

    Use this tool when the user provides a specific product ID and wants detailed information about that product.

    Parameters:
        id (str): The unique identifier of the product (case-sensitive or as stored in the dataset).

    Returns:
        str: A formatted string containing product details such as name, category, description, brand, etc.
    Errors:
        - Returns "Product not found." if the ID does not exist.
    """
    try:
        product = DF.loc[id]
        formatted_response = _format_product(product)
        return formatted_response
    except KeyError:
        return "Product not found."


# tool for search prodcut by category
@tool("product_search_category")
def product_search_category(category:str):
    """
    Search for products within a specific category.

    Use this tool when the user asks for products belonging to a general category.

    Parameters:
        category (str): The category name (case-insensitive).

    Returns:
        str: A formatted string containing all matching products in that category.

    Errors:
        - Returns "No products found in this category." if no matches exist.
    """
    products  = DF[DF['category']== category.lower()]

    if products.empty:
        return "No products found in this category."
    formatted_response = _format_products(products)
    return formatted_response


#tool for search product by sub categroy
@tool("product_search_sub_category")
def product_search_sub_category(sub_category:str):
    """
    Search for products within a specific sub-category.

    Use this tool when the user provides a more specific classification within a category.

    Parameters:
        sub_category (str): The sub-category name (case-insensitive).

    Returns:
        str: A formatted string containing all matching products in that sub-category.

    Errors:
        - Returns "No products found in this sub-category." if no matches exist.
    """
    products  = DF[DF['sub_category']== sub_category.lower()]

    if  products.empty:
        return "No products found in this sub-category."
    formatted_response = _format_products(products)
    return formatted_response


#tool for search product by brand
@tool("product_search_brand")
def product_search_brand(name:str):
    """
    Search for products by brand name.

    Use this tool when the user specifies a brand and wants to see all products from that brand.

    Parameters:
        name (str): The brand name (case-insensitive).

    Returns:
        str: A formatted string containing all products associated with the given brand.

    Errors:
        - Returns "No products found for this brand." if no matches exist.
    """
    products  = DF[DF['brand']== name.lower()]

    if products.empty:
        return "No products found for this brand."
    formatted_response = _format_products(products)
    return formatted_response


# format chroma name results
def format_chroma_results(docs, mode:str, limit=2):
    """
    Formats LangChain Document objects into a clean string for the LLM.
    
    Args:
        docs: List of Document objects from Chroma.
        mode: "name" or "description" - specifies which field was embedded.
        limit: Number of results to return.
    """
    if not docs:
        return "No results found in the database."
    
    formatted_results = []
    for i, doc in enumerate(docs[:limit]):
        metadata = doc.metadata
        
        # Determine Name and Description based on the mode
        if mode == "name":
            name = doc.page_content
            description = metadata.get('description', 'N/A')
        else:
            # If we searched by description, page_content is the description
            name = metadata.get('product_name', 'N/A')
            description = doc.page_content
            
        row_str = (
            f"Result {i+1}: "
            f"ID: {metadata.get('product_id', 'N/A')}, "
            f"Name: {name}, "
            f"Description: {description}, "
            f"Brand: {metadata.get('brand', 'N/A')}, "
            f"Category: {metadata.get('category', 'N/A')}, "
            f"Sub-Category: {metadata.get('sub_category', 'N/A')}, "
            f"Imported from: {metadata.get('Imported_from', 'N/A')}"
        )
        formatted_results.append(row_str)
        
    return "\n\n".join(formatted_results)


#tool for search product by name
@tool(description="prodcut_search_name")
def prodcut_search_name(prodcut_name:str):
    """
    Search for products based on their name.

    Use this tool when the user provides a product name or partial name.

    Parameters:
        product_name (str): The name or partial name of the product.

    Returns:
        str: A formatted string containing the top 2 most similar product matches.
    """
    result = product_name.similarity_search(query=prodcut_name, k=2)
    formatted_answer = format_chroma_results(result,"name")
    return formatted_answer


@tool(description="prodcut_search_description")
def prodcut_search_description(prodcut_description:str):
    """
    Search for products based on description, features, or use-case.

    Use this tool when the user describes what they are looking for instead of giving a product name.

    Parameters:
        product_description (str): A natural language description of the desired product.

    Returns:
        str: A formatted string containing the top 2 most relevant product matches.
    
    Notes:
        - Best for long, descriptive, or feature-based queries.
        - Prefer this over name search when the query is not an exact product name.
    """

    result = product_desc.similarity_search(query=prodcut_description, k=2)
    formatted_answer = format_chroma_results(result, "description")
    return formatted_answer
