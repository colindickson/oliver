import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Strip the async aiosqlite driver if the env var was copied from the backend config.
# The MCP server uses synchronous SQLAlchemy (stdio transport, no event loop needed).
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:////data/oliver.db").replace(
    "sqlite+aiosqlite://", "sqlite://"
)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
