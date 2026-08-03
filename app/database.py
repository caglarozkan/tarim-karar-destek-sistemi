from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os 

load_dotenv()

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:" + os.getenv("sifre") + "@localhost:3306/tarim_karar_analiz"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()