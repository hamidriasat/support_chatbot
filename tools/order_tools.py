import pandas as pd
from langchain.tools import tool
from utils.config import settings


DF_ORDER = None
DF_INVENTORY = None


def initialize():
    global DF_ORDER, DF_INVENTORY

    if DF_ORDER is not None and DF_INVENTORY is not None:
        return
    
    DF_ORDER = pd.read_csv(settings.get("ORDER_DATA_PATH"))
    DF_INVENTORY = pd.read_csv(settings.get("INVENTORY_DATA_PATH"))
    DF_ORDER.set_index("order_id", inplace=True)
    DF_INVENTORY.set_index("product_id", inplace=True)


def format_order_response(order):
    try:
        order_id = order.name
        product_ids = order.get("product_ids",[])
        prices = order.get("prices",[])
        order_date = order.get("order_date","")
        total_price = order.get("total_price","")
        delivery_charges = order.get("delivery_charges","")
        final_amount = order.get("final_amount","")
        status = order.get("status","")
        expected_delivery_date = order.get("expected_delivery_date","")
        payment_method = order.get("payment_method","")
        payment_status = order.get("payment_status","")
        address_detail = order.get("address_detail","")

        return f"ID: {order_id}, Products: {product_ids}, Prices breakdown: {prices}, Total price: {total_price}, Delivery charges: {delivery_charges}, Final amount: {final_amount}, Order data: {order_date}, Expected delivery date: {expected_delivery_date}, order status: {status}, Payment method: {payment_method}, Payment status: {payment_status}, Address: {address_detail}."
    except Exception as e:
        return f"Error formatting order details: {str(e)}"

# read order from csv
@tool("read_order")
def read_order(order_id: str):
    """
    Retrieve details of a specific order.

    Use this tool when you need to look up information about an order by its ID.

    Parameters:
        order_id (str): The unique identifier of the order (case-insensitive).

    Returns:
        str: A formatted string containing order details such as product info, status, etc.

    Errors:
        - Returns "order id not found" if the order does not exist.
    """
    initialize()
    try:
        order_detail = DF_ORDER.loc[order_id.lower()]
        return format_order_response(order_detail)
    except KeyError:
        return "order id not found"


# update the order
@tool(description="update_order")
def update_order(order_id: str, updates: dict):
    """
    Update one or more fields of an existing order in a single operation.

    Use this tool when you need to modify order information. Pass all related
    changes together (e.g., when adding a product, include product, price, 
    and total_price in the same call).

    Parameters:
        order_id (str): The unique identifier of the order (case-insensitive).
        updates (dict): A dictionary of {column: value} pairs to update.
                        Example: {"product": "Widget", "price": 9.99, "total_price": 29.97}

    Returns:
        str: Confirmation message if the update is successful.
    """
    initialize()
    try:
        for column, value in updates.items():
            target_dtype = DF_ORDER[column].dtype
            typed_value = value
            if "int" in str(target_dtype):
                typed_value = int(float(str(value)))
            elif "float" in str(target_dtype):
                typed_value = float(value)
            DF_ORDER.loc[order_id.lower(), column] = typed_value

        DF_ORDER.to_csv(settings.get("ORDER_DATA_PATH"), index=True)
        return f"Order updated successfully: {list(updates.keys())}"

    except KeyError:
        return "Order id does not exist."


def format_inventory_response(inventory):
    try:
        product_id = inventory.name
        price = inventory.get("price",0)
        size = inventory.get("size","")
        stock = inventory.get("stock",0)

        return f"Product id: {product_id}, Unit price: {price}, Product size: {size}, available stock: {stock}."
    except Exception as e:
        return f"Error formatting inventory details: {str(e)}" 


# inventory tool
@tool("read_inventory")
def read_inventory(product_id:str):
    """
    Retrieve inventory details for a specific product using its ID.

    Use this tool when you already have an exact product_id and need stock or inventory information.

    Parameters:
        product_id (str): The unique identifier of the product (case-insensitive).

    Returns:
        str: A formatted string containing inventory details (e.g., stock level, availability, etc.).

    Errors:
        - Returns "product not found" if the product_id does not exist.
    """
    initialize()
    try:
        inventory = DF_INVENTORY.loc[product_id.lower()]
        return format_inventory_response(inventory)
    except KeyError:
        return "product not found"
