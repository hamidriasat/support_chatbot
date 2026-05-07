from pydantic import BaseModel

class ResponseModel(BaseModel):
    response: str
    waiting_for_approval: bool = False


class VoiceResponseModel(ResponseModel):
    transcription: str
    audio: str