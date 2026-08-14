from pydantic import BaseModel

class ChatRequest(BaseModel):
    conversation_id: int
    query: str

class UploadResponse(BaseModel):
    message: str
    num_docs: int
