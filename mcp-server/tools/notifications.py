"""MCP tool for creating notifications visible in the Oliver UI."""

import json
from tools.daily import get_session
from tools.log_utils import log_call
from models.notification import Notification


def notify(source: str, content: str) -> str:
    """Create a notification visible in the Oliver UI."""
    params = {"source": source, "content": content}
    try:
        with get_session() as session:
            n = Notification(source=source[:100], content=content[:500])
            session.add(n)
            session.commit()
            session.refresh(n)
        result_json = json.dumps({"id": n.id, "source": n.source, "content": n.content})
        log_call("notify", params, result_json, "success", before_state=None)
        return result_json
    except Exception as e:
        error_json = json.dumps({"error": str(e)})
        log_call("notify", params, error_json, "error")
        return error_json
