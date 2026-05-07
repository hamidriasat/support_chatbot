from pydantic import BaseModel


class InputTextModel(BaseModel):
    message: str
    chat_id: str