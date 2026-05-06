from utils.config import settings
from psycopg_pool import ConnectionPool
from psycopg import Connection
from langgraph.checkpoint.postgres import PostgresSaver


def connection():
    conn_string = settings.get("DB_URI","")
    if not conn_string or conn_string == "":
        raise ValueError("DB_URI is not set in the configuration.")
    
    pool = ConnectionPool(conninfo=conn_string)
    return pool


def setup_postgres_saver():

    conn_string = settings.get("DB_URI","")

    if not conn_string or conn_string == "":
        raise ValueError("DB_URI is not set in the configuration.")
    
    with Connection.connect(conn_string, autocommit=True) as conn:
        checkpointer = PostgresSaver(conn)
        
        print("Checking/Setting up LangGraph tables...")
        checkpointer.setup()
        print("Setup complete.")


if __name__ == "__main__":
    setup_postgres_saver()