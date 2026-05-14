from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    query: str

class Citation(BaseModel):
    chunk_id: str
    text: str
    images_base64: List[str] = []  
    tables_html: List[str] = []    

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]