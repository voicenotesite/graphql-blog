from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from app.database import engine, Base, get_db
from app.schema import schema
from app.auth import get_current_user
from app.models import User

Base.metadata.create_all(bind=engine)

async def get_context(db: Session = Depends(get_db)):
    return {"db": db}

graphql_router = GraphQLRouter(schema, context_getter=get_context)

app = FastAPI(title="GraphQL Blog API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(graphql_router, prefix="/graphql")

@app.get("/health")
def health():
    return {"status": "ok"}
