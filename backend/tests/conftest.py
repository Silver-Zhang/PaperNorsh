"""Shared pytest fixtures for the PaperNosh test suite."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.preference import UserPreference
from app.models.user import User

# Use SQLite in-memory for tests
_SQLITE_URL = "sqlite://"

engine = create_engine(_SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_user(db) -> User:
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def sample_preferences(db, sample_user) -> UserPreference:
    pref = UserPreference(
        user_id=sample_user.id,
        keywords=["machine learning", "neural networks"],
        exclude_keywords=["spam", "advertisement"],
        follow_authors=["Yann LeCun", "Geoffrey Hinton"],
        preferred_sources=["arxiv", "openalex", "crossref"],
        preferred_journals=["Nature", "Science"],
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


@pytest.fixture()
def auth_headers(client, sample_user) -> dict:
    resp = client.post(
        "/api/auth/login",
        data={"username": sample_user.email, "password": "password123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
