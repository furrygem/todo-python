from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from . import config


# URL = "sqlite:///db.sqlite3"
URL = config.database_url

engine = create_engine(URL, echo=True, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base(bind=engine)
