from sqlalchemy import create_engine, Column, Integer, String, DateTime, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import datetime
import os

# Load environment variables from .env
load_dotenv()
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Render automatically provides DATABASE_URL when database is linked
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback for local development
    DATABASE_URL = "postgresql+psycopg2://postgres:aadimilihani@localhost:5432/intelliject"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# History table model
class PDFHistory(Base):
    _tablename_ = "pdf_history"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    _table_args_ = (
        Index("idx_pdf_history_subject", "subject"),
        Index("idx_pdf_history_timestamp", "timestamp"),
    )

    def _repr_(self):
        return (
            f"<PDFHistory(id={self.id}, filename='{self.filename}', "
            f"subject='{self.subject}', timestamp={self.timestamp})>"
        )