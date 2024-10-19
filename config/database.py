from sqlalchemy import create_engine
from sqlmodel import SQLModel, create_engine

sql_file_name = 'database.sqlite'
sqllite_url = f'sqlite:///{sql_file_name}'

engine = create_engine(sqllite_url, echo=True)

def create_db_and_tables():
    from models import Option, Poll, Vote
    SQLModel.metadata.create_all(engine)