from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, portfolios, reports
from .database import Base, engine

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    Base.metadata.create_all(bind=engine)
    yield
    

app = FastAPI(title="HRP Portfolio API", lifespan=lifespan)

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


