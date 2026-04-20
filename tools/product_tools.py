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
    search the product by id
    return the product information
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
    product search by category
    return products from searched category
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
    product search by sub-category
    return products from searched sub category
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
    product search by brand name
    return products from searched brand
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
    take prodcut_name as input and return the top 2 results
    """
    result = product_name.similarity_search(query=prodcut_name, k=2)
    formatted_answer = format_chroma_results(result,"name")
    return formatted_answer


@tool(description="prodcut_search_description")
def prodcut_search_description(prodcut_description:str):
    """
    Take prodcut_description as input and return top 2 results
    """

    result = product_desc.similarity_search(query=prodcut_description, k=2)
    formatted_answer = format_chroma_results(result, "description")
    return formatted_answer
