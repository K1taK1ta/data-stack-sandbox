from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine, String, MetaData
from typing import Annotated
import os
from dotenv import load_dotenv
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

sync_engine = create_engine(
    url=DATABASE_URL,
    echo=False,
    # pool_size=5,
    # max_overflow=10
    )

session_factory = sessionmaker(sync_engine)
str_512 = Annotated[str, 512]
metadata_obj = MetaData(schema="mcp_app")

class Base(DeclarativeBase):
    metadata = metadata_obj

    type_annotation_map = {
        str_512: String(512)
    }