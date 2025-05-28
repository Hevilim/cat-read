from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from  .models import Base

DATABASE_URL = "sqlite:///cat.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# Инициализация базы данных
def init_db():
    Base.metadata.create_all(bind=engine)


# Dependency для получения сессии через context manager
def get_db():
    with SessionLocal() as db:
        yield db