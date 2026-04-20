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


@tool("order_manager")
def order_manager(order_id: str):
    """
    takes the order_id and return the string containing information about that order.
    """
    initialize()
    try:
        order_detail = DF_ORDER.loc[order_id.lower()]
        return format_order_response(order_detail)
    except KeyError:
        return "order id not found"


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
@tool("inventory_manager")
def inventory_manager(product_id:str):
    """
    """
    initialize()
    try:
        inventory = DF_INVENTORY.loc[product_id.lower()]
        return format_inventory_response(inventory)
    except KeyError:
        return "product not found"
