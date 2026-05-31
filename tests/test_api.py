import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

REGISTER = """
mutation($input: RegisterInput!) {
  register(input: $input) { accessToken user { id email username } }
}
"""
LOGIN = """
mutation($input: LoginInput!) {
  login(input: $input) { accessToken user { id email username } }
}
"""
CREATE_POST = """
mutation($input: CreatePostInput!) {
  createPost(input: $input) { id title content published author { username } }
}
"""
GET_POSTS = """
query { posts { id title content author { username } comments { content author { username } } } }
"""
ADD_COMMENT = """
mutation($input: CreateCommentInput!) {
  addComment(input: $input) { id content author { username } }
}
"""

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

client = TestClient(app)

def gql(query: str, variables: dict = None, token: str = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = {"query": query}
    if variables:
        body["variables"] = variables
    return client.post("/graphql", json=body, headers=headers).json()

def test_health():
    r = client.get("/health")
    assert r.status_code == 200

def test_register_and_login():
    r = gql(REGISTER, {"input": {"email": "a@a.pl", "username": "alice", "password": "pass123"}})
    assert "errors" not in r
    token = r["data"]["register"]["accessToken"]
    assert token
    assert r["data"]["register"]["user"]["username"] == "alice"

    r = gql(LOGIN, {"input": {"email": "a@a.pl", "password": "pass123"}})
    assert "errors" not in r
    assert r["data"]["login"]["accessToken"] == token

def test_crud_post():
    r = gql(REGISTER, {"input": {"email": "b@b.pl", "username": "bob", "password": "pass456"}})
    token = r["data"]["register"]["accessToken"]

    r = gql(CREATE_POST, {"input": {"title": "Hello World", "content": "First post!", "published": True}}, token)
    assert "errors" not in r
    post_id = r["data"]["createPost"]["id"]
    assert r["data"]["createPost"]["title"] == "Hello World"

    r = gql(GET_POSTS)
    assert "errors" not in r
    assert len(r["data"]["posts"]) == 1
    assert r["data"]["posts"][0]["title"] == "Hello World"
    assert r["data"]["posts"][0]["author"]["username"] == "bob"

    r = gql(ADD_COMMENT, {"input": {"postId": post_id, "content": "Nice post!"}}, token)
    assert "errors" not in r, r
    assert r["data"]["addComment"]["content"] == "Nice post!"

    r = gql(GET_POSTS)
    assert len(r["data"]["posts"][0]["comments"]) == 1
