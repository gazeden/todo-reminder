from typing import Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlmodel import Session, select, func

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base CRUD class with common database operations.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        statement = select(self.model).where(self.model.id == id)
        return db.exec(statement).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination."""
        statement = select(self.model).offset(skip).limit(limit)
        return list(db.exec(statement).all())

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update an existing record."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Delete a record by ID."""
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def count(self, db: Session) -> int:
        """Count total records."""
        statement = select(func.count()).select_from(self.model)
        return db.exec(statement).one()
