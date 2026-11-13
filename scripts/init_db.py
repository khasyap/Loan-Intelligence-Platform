import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.connection import engine, Base
from backend.app.models.entities import *

def init_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print(f"Successfully initialized {len(Base.metadata.tables)} tables in database:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")

if __name__ == "__main__":
    init_database()
