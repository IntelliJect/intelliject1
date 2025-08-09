from sqlalchemy import create_engine, Column, Integer, String, DateTime, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import datetime
import os

# Load environment variables from .env
load_dotenv()

# Create the database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://username:password@localhost:5432/intelliject"
)

# Setup engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Declare Base
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