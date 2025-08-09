import os
import json
from database import SessionLocal
import crud


def load_pyqs_from_json(json_path: str, subject: str):
    with open(json_path, "r", encoding="utf-8") as f:
        pyqs = json.load(f)

    try:
        with SessionLocal() as db:
            crud.store_pyqs(db, pyqs, subject)
        print(f"✅ Inserted {len(pyqs)} PYQs for subject: {subject}")
    except Exception as e:
        print(f"❌ Error inserting data for {subject}: {e}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    subjects_dir = os.path.join(current_dir, "subjects")

    if not os.path.exists(subjects_dir):
        print(f"❌ 'subjects' folder not found at: {subjects_dir}")
        exit(1)

    json_files = [f for f in os.listdir(subjects_dir) if f.endswith(".json")]
    if not json_files:
        print("❌ No JSON files found in the 'subjects' folder.")
        exit(1)

    for filename in json_files:
        subject_name = os.path.splitext(filename)[0]
        path = os.path.join(subjects_dir, filename)
        print(f"📥 Loading {filename} for subject: {subject_name}")
        load_pyqs_from_json(path, subject_name)
