"""
FastAPI application entry point.
Run with:  uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth as auth_router
from .routers import transactions as transactions_router
from .routers import upload as upload_router
from .routers import dashboard as dashboard_router
from .routers import ml as ml_router
from .routers import assistant as assistant_router

# Create all database tables on startup (SQLite file finance.db)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Personal Finance Tracker API",
    description="Backend for the AI-powered Personal Finance Tracker",
    version="1.0.0",
)

# Allow the React dev server (default Vite port 5173, CRA port 3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(
    transactions_router.router, prefix="/api/transactions", tags=["Transactions"]
)
app.include_router(upload_router.router, prefix="/api/upload", tags=["Upload"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(ml_router.router, prefix="/api/ml", tags=["Machine Learning"])
app.include_router(assistant_router.router, prefix="/api/assistant", tags=["AI Assistant"])


@app.get("/")
def root():
    return {"message": "AI Personal Finance Tracker API is running"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
