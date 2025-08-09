from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class PYQ(Base):
    __tablename__ = "pyqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, index=True)
    year = Column(String)
    semester = Column(String)
    branch = Column(String)
    unit = Column(String)
    marks = Column(Float)  # To support 2.5 marks
    sub_topic = Column(String, index=True)
    subject = Column(String, nullable=False)

class PDFHistory(Base):
    __tablename__ = "pdf_history"
    __table_args__ = {'extend_existing': True}  # ✅ Fix here

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    subject = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
