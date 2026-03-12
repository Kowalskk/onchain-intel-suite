from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.routes import trace, wallet
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🌞 Starting {settings.APP_NAME} — Solana Forensic Tracer")
    yield
    print("Shutting down Solarized...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Solarized — Solana Forensic Tracing Tool. Visualize wallet fund flows with Helius.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for local dev; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(trace.router)
app.include_router(wallet.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "description": "Solana Forensic Tracer",
        "docs": "/docs",
        "health": "/health",
    }
