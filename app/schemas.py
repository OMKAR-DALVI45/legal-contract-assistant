from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    citation: int
    document_id: str
    document_name: str
    page: int
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
