"""
server.py — FastAPI server kết nối frontend với ReAct agent.
Chạy: python server.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from src.agent.agent import run_agent, chat_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    student_name: str = ""
    student_id:   str = ""
    id_card:      str = ""
    semester:     str = "Spring 2026"

class ChatRequest(BaseModel):
    message: str

@app.post("/query")
def query_student(req: QueryRequest):
    """Direct lookup — dùng cho sidebar quick cases."""
    result = run_agent(
        student_id=req.student_id,
        student_name=req.student_name,
        id_card=req.id_card,
        semester=req.semester,
    )
    return {"result": result}

@app.post("/chat")
def chat(req: ChatRequest):
    """Chat mode — LLM tự hiểu câu hỏi và gọi tool."""
    result = chat_agent(req.message)
    return {"result": result}

@app.get("/")
def serve_frontend():
    return FileResponse("frontend.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)