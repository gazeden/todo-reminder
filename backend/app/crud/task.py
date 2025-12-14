import calendar
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.crud.base import CRUDBase
from app.models.task import RecurrenceUnit, Task, TaskCompletion, TaskStatus
from app.schemas.task import TaskCreate, TaskStatsResponse, TaskUpdate
from sqlmodel import Session, func, select


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    """
    CRUD operations for Task model with flexible scheduling.
    """

    def get_by_owner(
        self,
        db: Session,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        include_inactive: bool = False,
    ) -> List[Task]:
        """Get all tasks for a specific owner."""
        statement = select(Task).where(Task.owner_id == owner_id)

        if not include_inactive:
            statement = statement.where(Task.is_active)

        if status:
            statement = statement.where(Task.status == status)

        statement = statement.offset(skip).limit(limit).order_by(Task.next_due_date)

        return list(db.exec(statement).all())

    def get_due_tasks(
        self, db: Session, *, owner_id: int, due_before: Optional[datetime] = None
    ) -> List[Task]:
        """Get tasks that are due."""
        if due_before is None:
            due_before = datetime.now(timezone.utc)

        statement = (
            select(Task)
            .where(Task.owner_id == owner_id)
            .where(Task.is_active)
            .where(Task.status == TaskStatus.PENDING)
            .where(Task.next_due_date <= due_before)
            .order_by(Task.next_due_date)
        )

        return list(db.exec(statement).all())

    def get_overdue_tasks(self, db: Session, *, owner_id: int) -> List[Task]:
        """Get overdue tasks."""
        now = datetime.now(timezone.utc)

        statement = (
            select(Task)
            .where(Task.owner_id == owner_id)
            .where(Task.is_active)
            .where(Task.status == TaskStatus.PENDING)
            .where(Task.next_due_date < now)
        )

        return list(db.exec(statement).all())

    def create_with_owner(
        self, db: Session, *, obj_in: TaskCreate, owner_id: int
    ) -> Task:
        """Create a new task with owner ID and calculate next due date."""
        task_data = obj_in.model_dump()
        task_data["owner_id"] = owner_id

        # Calculate next due date
        next_due = self._calculate_next_due_date(
            is_recurring=obj_in.is_recurring,
            recurrence_interval=obj_in.recurrence_interval,
            recurrence_unit=obj_in.recurrence_unit,
            specific_days_of_week=obj_in.specific_days_of_week,
            specific_days_of_month=obj_in.specific_days_of_month,
            reminder_time=obj_in.reminder_time,
        )
        task_data["next_due_date"] = next_due

        db_obj = Task(**task_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def complete_task(
        self, db: Session, *, task_id: int, notes: Optional[str] = None
    ) -> Task:
        """Mark task as completed and create completion record."""
        task = self.get(db, id=task_id)
        if not task:
            return None

        now = datetime.now(timezone.utc)

        # Create completion record
        completion = TaskCompletion(task_id=task_id, completed_at=now, notes=notes)
        db.add(completion)

        # Update task
        task.completed_at = now
        task.last_completed_date = now

        # If recurring, calculate next due date and set to pending
        if task.is_recurring:
            task.next_due_date = self._calculate_next_due_date(
                is_recurring=task.is_recurring,
                recurrence_interval=task.recurrence_interval,
                recurrence_unit=task.recurrence_unit,
                specific_days_of_week=task.specific_days_of_week,
                specific_days_of_month=task.specific_days_of_month,
                reminder_time=task.reminder_time,
                from_date=now,
            )
            task.status = TaskStatus.PENDING
        else:
            # One-time task, mark as completed
            task.status = TaskStatus.COMPLETED

        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get_completions(
        self, db: Session, *, task_id: int, limit: int = 50
    ) -> List[TaskCompletion]:
        """Get completion history for a task."""
        statement = (
            select(TaskCompletion)
            .where(TaskCompletion.task_id == task_id)
            .order_by(TaskCompletion.completed_at.desc())
            .limit(limit)
        )
        return list(db.exec(statement).all())

    def get_stats(self, db: Session, *, owner_id: int) -> TaskStatsResponse:
        """Get task statistics for a user."""
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day)

        # Total tasks
        total = db.exec(
            select(func.count())
            .select_from(Task)
            .where(Task.owner_id == owner_id)
            .where(Task.is_active)
        ).one()

        # Pending tasks
        pending = db.exec(
            select(func.count())
            .select_from(Task)
            .where(Task.owner_id == owner_id)
            .where(Task.is_active)
            .where(Task.status == TaskStatus.PENDING)
        ).one()

        # Completed today
        completed_today = db.exec(
            select(func.count())
            .select_from(TaskCompletion)
            .join(Task)
            .where(Task.owner_id == owner_id)
            .where(TaskCompletion.completed_at >= today_start)
        ).one()

        # Overdue tasks
        overdue = db.exec(
            select(func.count())
            .select_from(Task)
            .where(Task.owner_id == owner_id)
            .where(Task.is_active)
            .where(Task.status == TaskStatus.PENDING)
            .where(Task.next_due_date < now)
        ).one()

        # Completion rate (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        completions_30d = db.exec(
            select(func.count())
            .select_from(TaskCompletion)
            .join(Task)
            .where(Task.owner_id == owner_id)
            .where(TaskCompletion.completed_at >= thirty_days_ago)
        ).one()

        completion_rate = (completions_30d / 30) if completions_30d > 0 else 0.0

        # Streak calculation
        streak = self._calculate_streak(db, owner_id=owner_id)

        return TaskStatsResponse(
            total_tasks=total,
            pending_tasks=pending,
            completed_today=completed_today,
            overdue_tasks=overdue,
            completion_rate=round(completion_rate, 2),
            streak_days=streak,
        )

    def _calculate_streak(self, db: Session, *, owner_id: int) -> int:
        """Calculate completion streak in days."""
        now = datetime.now(timezone.utc)
        streak = 0

        for i in range(365):  # Max 365 day streak
            day_start = datetime(now.year, now.month, now.day) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            # Check if any task was completed on this day
            completed = db.exec(
                select(func.count())
                .select_from(TaskCompletion)
                .join(Task)
                .where(Task.owner_id == owner_id)
                .where(TaskCompletion.completed_at >= day_start)
                .where(TaskCompletion.completed_at < day_end)
            ).one()

            if completed > 0:
                streak += 1
            else:
                break

        return streak

    def _calculate_next_due_date(
        self,
        is_recurring: bool,
        recurrence_interval: Optional[int],
        recurrence_unit: Optional[RecurrenceUnit],
        specific_days_of_week: Optional[List[int]],
        specific_days_of_month: Optional[List[int]],
        reminder_time: Optional[str],
        from_date: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """
        Calculate next due date based on flexible recurrence settings.

        Supports:
        - Interval-based: Every N days/weeks/months
        - Specific weekdays: Every Tuesday and Thursday
        - Specific month days: 1st and 15th of every month
        - Combination: Every 2 weeks on Monday and Wednesday
        """
        if from_date is None:
            from_date = datetime.now(timezone.utc)

        # Non-recurring task: due immediately or at specified time
        if not is_recurring:
            if reminder_time:
                hour, minute = map(int, reminder_time.split(":"))
                return datetime(
                    from_date.year, from_date.month, from_date.day, hour, minute
                )
            return from_date

        # Parse reminder time
        target_hour = 9  # Default 9 AM
        target_minute = 0
        if reminder_time:
            target_hour, target_minute = map(int, reminder_time.split(":"))

        # Case 1: Specific days of week (e.g., every Tuesday and Thursday)
        if specific_days_of_week and len(specific_days_of_week) > 0:
            return self._calculate_next_weekday_occurrence(
                from_date=from_date,
                target_weekdays=specific_days_of_week,
                interval_weeks=recurrence_interval
                if recurrence_unit == RecurrenceUnit.WEEKS
                else None,
                hour=target_hour,
                minute=target_minute,
            )

        # Case 2: Specific days of month (e.g., 1st and 15th)
        if specific_days_of_month and len(specific_days_of_month) > 0:
            return self._calculate_next_monthday_occurrence(
                from_date=from_date,
                target_days=specific_days_of_month,
                interval_months=recurrence_interval
                if recurrence_unit == RecurrenceUnit.MONTHS
                else None,
                hour=target_hour,
                minute=target_minute,
            )

        # Case 3: Interval-based (every N days/weeks/months)
        if recurrence_interval and recurrence_unit:
            return self._calculate_interval_based(
                from_date=from_date,
                interval=recurrence_interval,
                unit=recurrence_unit,
                hour=target_hour,
                minute=target_minute,
            )

        # Fallback: due now
        return from_date

    def _calculate_next_weekday_occurrence(
        self,
        from_date: datetime,
        target_weekdays: List[int],
        interval_weeks: Optional[int],
        hour: int,
        minute: int,
    ) -> datetime:
        """
        Calculate next occurrence for specific weekdays.

        Args:
            from_date: Starting date
            target_weekdays: List of weekday numbers (0=Monday, 6=Sunday)
            interval_weeks: If set, only consider every Nth week (e.g., 2 = biweekly)
            hour: Target hour
            minute: Target minute
        """
        current_weekday = from_date.weekday()
        sorted_weekdays = sorted(target_weekdays)

        # Find next target weekday
        next_weekdays = [d for d in sorted_weekdays if d > current_weekday]

        if next_weekdays:
            # Next occurrence is this week
            days_ahead = next_weekdays[0] - current_weekday
        else:
            # Next occurrence is next week (or next interval week)
            days_ahead = (7 - current_weekday) + sorted_weekdays[0]
            if interval_weeks and interval_weeks > 1:
                # Add additional weeks for interval
                days_ahead += 7 * (interval_weeks - 1)

        next_date = from_date + timedelta(days=days_ahead)
        return datetime(next_date.year, next_date.month, next_date.day, hour, minute)

    def _calculate_next_monthday_occurrence(
        self,
        from_date: datetime,
        target_days: List[int],
        interval_months: Optional[int],
        hour: int,
        minute: int,
    ) -> datetime:
        """
        Calculate next occurrence for specific days of month.

        Args:
            from_date: Starting date
            target_days: List of day numbers (1-31)
            interval_months: If set, only consider every Nth month
            hour: Target hour
            minute: Target minute
        """
        current_day = from_date.day
        sorted_days = sorted(target_days)

        # Find next target day this month
        next_days_this_month = [d for d in sorted_days if d > current_day]

        if next_days_this_month:
            # Check if day exists in current month
            max_day = calendar.monthrange(from_date.year, from_date.month)[1]
            target_day = next_days_this_month[0]

            if target_day <= max_day:
                return datetime(
                    from_date.year, from_date.month, target_day, hour, minute
                )

        # Next occurrence is in next month (or next interval month)
        months_ahead = interval_months if interval_months else 1

        next_month = from_date.month + months_ahead
        next_year = from_date.year

        while next_month > 12:
            next_month -= 12
            next_year += 1

        # Get first valid day in target month
        max_day = calendar.monthrange(next_year, next_month)[1]
        target_day = min(sorted_days[0], max_day)

        return datetime(next_year, next_month, target_day, hour, minute)

    def _calculate_interval_based(
        self,
        from_date: datetime,
        interval: int,
        unit: RecurrenceUnit,
        hour: int,
        minute: int,
    ) -> datetime:
        """
        Calculate next occurrence for interval-based recurrence.

        Args:
            from_date: Starting date
            interval: Number of units
            unit: Time unit (days/weeks/months)
            hour: Target hour
            minute: Target minute
        """
        if unit == RecurrenceUnit.DAYS:
            next_date = from_date + timedelta(days=interval)
            return datetime(
                next_date.year, next_date.month, next_date.day, hour, minute
            )

        elif unit == RecurrenceUnit.WEEKS:
            next_date = from_date + timedelta(weeks=interval)
            return datetime(
                next_date.year, next_date.month, next_date.day, hour, minute
            )

        elif unit == RecurrenceUnit.MONTHS:
            # Add months
            month = from_date.month + interval
            year = from_date.year

            while month > 12:
                month -= 12
                year += 1

            # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
            max_day = calendar.monthrange(year, month)[1]
            day = min(from_date.day, max_day)

            return datetime(year, month, day, hour, minute)

        return from_date


task_crud = CRUDTask(Task)
