from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    thread_id: str = "default_thread"

class UploadResponse(BaseModel):
    message: str
    num_docs: int
