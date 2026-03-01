"""MCP tool for creating notifications visible in the Oliver UI."""

import json
from tools.daily import get_session
from models.notification import Notification


def notify(source: str, content: str) -> str:
    """Create a notification visible in the Oliver UI."""
    with get_session() as session:
        n = Notification(source=source, content=content[:500])
        session.add(n)
        session.commit()
        session.refresh(n)
    return json.dumps({"id": n.id, "source": n.source, "content": n.content})
