"""Model registry — import all ORM models so Alembic can discover them.

All models must be imported here before ``Base.metadata`` is used for
``create_all`` or Alembic autogenerate.
"""

from app.models.daily_note import DailyNote
from app.models.day import Day
from app.models.day_metadata import DayMetadata
from app.models.day_off import DayOff
from app.models.day_rating import DayRating
from app.models.goal import Goal
from app.models.reminder import Reminder
from app.models.roadblock import Roadblock
from app.models.setting import Setting
from app.models.tag import Tag
from app.models.task import Task
from app.models.task_template import TaskTemplate
from app.models.timer_session import TimerSession

__all__ = [
    "DailyNote",
    "Day",
    "DayMetadata",
    "DayOff",
    "DayRating",
    "Goal",
    "Reminder",
    "Roadblock",
    "Setting",
    "Tag",
    "Task",
    "TaskTemplate",
    "TimerSession",
]
