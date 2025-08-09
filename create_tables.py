from database import Base, engine
from database import PDFHistory  # Or your other models

Base.metadata.create_all(bind=engine)
