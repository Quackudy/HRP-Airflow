from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, portfolios, reports
from .database import Base, engine


app = FastAPI(title="HRP Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
app.include_router(reports.router, prefix="/portfolios", tags=["reports"])


@app.on_event("startup")
def on_startup():
    # Create tables if not exist (for quickstart/dev). In prod, use Alembic migrations.
    Base.metadata.create_all(bind=engine)


