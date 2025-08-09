from sqlalchemy.orm import Session
from typing import List, Dict
import models

def get_pyqs_by_subject(db: Session, subject: str) -> List[models.PYQ]:
    """
    Retrieve all PYQ entries for the given subject.
    """
    return db.query(models.PYQ).filter(models.PYQ.subject == subject).all()


def store_pyqs(db: Session, pyqs: List[Dict], subject: str) -> int:
    """
    Store a list of PYQs in the database under the given subject.
    Returns the number of successfully inserted records.
    """
    pyq_objects = []
    for entry in pyqs:
        # Basic validation
        question = entry.get("question")
        if not question:
            continue  # skip invalid entries or raise error as needed

        pyq_obj = models.PYQ(
            subject=subject,
            sub_topic=entry.get("sub_topic", ""),
            question=question,
            marks=entry.get("marks", 0),
            year=entry.get("year", ""),
        )
        pyq_objects.append(pyq_obj)

    try:
        db.add_all(pyq_objects)
        db.commit()
        return len(pyq_objects)
    except Exception as e:
        db.rollback()
        print(f"Error storing PYQs: {e}")
        return 0

