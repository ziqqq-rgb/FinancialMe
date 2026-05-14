import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import pipeline

app = FastAPI(
    title="FinancialMe Enterprise RAG",
    description="Multi-Modal RAG API for Financial Documents",
    version="1.0.0"
)

# Configure CORS to allow the Next.js frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Default Next.js port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach our RAG routes
app.include_router(pipeline.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "FinancialMe Backend API"}

if __name__ == "__main__":
    print("Starting FinancialMe Backend Server...")
    # Run the server on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)