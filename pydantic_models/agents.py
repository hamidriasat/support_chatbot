from pydantic import BaseModel, Field
from typing import List



class Router(BaseModel):
    category: List[str] = Field(description="which category or categories, the question belong to.")
    reasoning: str = Field(description="write the reason why you choose the category or categories")

