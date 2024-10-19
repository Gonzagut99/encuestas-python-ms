from datetime import datetime
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from models.Option import Option
from utils.uuid import get_default_uuid

class Poll(SQLModel, table=True):
    id: Optional[str] = Field(
        default_factory= get_default_uuid,
        primary_key=True,
    )    
    poll_text: str = Field(default=None, min_length=1, max_length=255)
    pub_date: datetime = Field(default_factory=datetime.now)
    user_id: str = Field(default=None, nullable=False)
    options: list[Option] = Relationship(
        back_populates="poll",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    
class PollCreateBody(SQLModel):
    poll_text: str
    options: list[str]  = Field(
        default=None,
        min_length=2,
        max_length=255,
        min_items=2,
        max_items=5,
    )
    
    model_config = {
        "example": {
            "poll_text": "¿Cuál es tu lenguaje de programación favorito?",
            "options": [
                "Python",
                "JavaScript",
                "Java",
                "Go",
                "C#"
            ]
        }    
    }