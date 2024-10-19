from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from utils.uuid import get_default_uuid

class Vote (SQLModel, table=True):
    id: Optional[str] = Field(
        default_factory= get_default_uuid,
        primary_key=True,
    )
    user_id: str = Field(default=None, nullable=False)
    option_id: str = Field(
        default=None, 
        foreign_key="option.id",
        nullable=False
    )
    option: "Option" = Relationship(back_populates="votes")
    
    