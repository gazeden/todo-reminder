import logging
from typing import Any, List, Optional

from app.api.deps import CommonQueryParams, get_current_active_user, get_db
from app.crud.task import task_crud
from app.kafka.utils.publishers import publish_event
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.kafka_events import (
    TaskCreatedEvent,
    TaskDeletedEvent,
    TaskUpdatedEvent,
    TaskCompletedEvent
)
from app.schemas.task import (
    TaskCompleteRequest,
    TaskCompletionResponse,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatsResponse,
    TaskUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    db: Session = Depends(get_db),
    commons: CommonQueryParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    include_inactive: bool = Query(False, description="Include inactive tasks"),
) -> Any:
    """
    Retrieve tasks for current user.
    """
    tasks = task_crud.get_by_owner(
        db,
        owner_id=current_user.id,
        skip=commons.skip,
        limit=commons.limit,
        status=status,
        include_inactive=include_inactive,
    )

    # Count total (for pagination)
    from app.models.task import Task
    from sqlmodel import func, select

    count_stmt = (
        select(func.count()).select_from(Task).where(Task.owner_id == current_user.id)
    )
    if not include_inactive:
        count_stmt = count_stmt.where(Task.is_active)
    if status:
        count_stmt = count_stmt.where(Task.status == status)

    total = db.exec(count_stmt).one()

    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=commons.skip // commons.limit + 1,
        page_size=commons.limit,
    )


@router.get("/due", response_model=list[TaskResponse])
async def get_due_tasks(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get tasks that are currently due.
    """
    tasks = task_crud.get_due_tasks(db, owner_id=current_user.id)
    return tasks


@router.get("/overdue", response_model=list[TaskResponse])
async def get_overdue_tasks(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get overdue tasks.
    """
    tasks = task_crud.get_overdue_tasks(db, owner_id=current_user.id)
    return tasks


@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get task statistics for current user.
    """
    stats = task_crud.get_stats(db, owner_id=current_user.id)
    return stats


@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get task by ID.
    """
    task = task_crud.get(db, id=task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new task.
    """
    # Create in DB
    task = task_crud.create_with_owner(db, obj_in=task_in, owner_id=current_user.id)

    # Publish event to Kafka
    publish_event("task.created", TaskCreatedEvent.from_task(task), key=str(task.id))

    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a task.
    """
    task = task_crud.get(db, id=task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    # Update task in DB
    task = task_crud.update(db, db_obj=task, obj_in=task_in)

    # Get changed fields
    def get_changed_fields(task: Task, task_update: TaskUpdate) -> List[str]:
        update_data = task_update.model_dump(exclude_unset=True)

        changed_fields: List[str] = []
        for field, new_value in update_data.items():
            old_value = getattr(task, field)
            if old_value != new_value:
                changed_fields.append(field)
        
        return changed_fields
    
    changed_fields = get_changed_fields(task, task_in)

    # Publish event to Kafka
    publish_event("task.updated", TaskUpdatedEvent.from_task(task, changed_fields), key=str(task.id))

    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    complete_data: TaskCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Mark task as completed.
    """
    task = task_crud.get(db, id=task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    # Create Task Completion in DB
    task = task_crud.complete_task(db, task_id=task_id, notes=complete_data.notes)

    # Publish event to Kafka
    publish_event("task.completed", TaskCompletedEvent.from_task(task, complete_data.notes), key=str(task.id))

    return task


@router.get("/{task_id}/completions", response_model=list[TaskCompletionResponse])
async def get_task_completions(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    """
    Get completion history for a task.
    """
    task = task_crud.get(db, id=task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    completions = task_crud.get_completions(db, task_id=task_id, limit=limit)
    return completions


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete a task.
    """
    task = task_crud.get(db, id=task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    # Delete task from DB
    task_crud.delete(db, id=task_id)

    # Publish event to Kafka
    publish_event("task.deleted", TaskDeletedEvent.from_task(task), key=str(task.id))
