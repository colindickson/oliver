"""Model registry — import all ORM models so Alembic can discover them.

All models must be imported here before ``Base.metadata`` is used for
``create_all`` or Alembic autogenerate.
"""

from app.models.day import Day
from app.models.reminder import Reminder
from app.models.setting import Setting
from app.models.task import Task
from app.models.timer_session import TimerSession

__all__ = [
    "Day",
    "Reminder",
    "Setting",
    "Task",
    "TimerSession",
]
