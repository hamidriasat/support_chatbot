from pydantic import BaseModel


class InputModel(BaseModel):
    message: str
    chat_id: str