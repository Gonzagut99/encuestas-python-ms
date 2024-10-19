from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from utils.uuid import get_default_uuid

class Option(SQLModel, table = True):
    id: Optional[str] = Field(
        default_factory= get_default_uuid,
        primary_key=True,
    )
    option_text: str = Field(default=None, min_length=1, max_length=255)
    poll_id: str = Field(
        foreign_key="poll.id",
        default=None,
    )
    poll: "Poll" = Relationship(
        back_populates="options"
    )
    votes: list[Optional["Vote"]] = Relationship(
        back_populates="option",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )