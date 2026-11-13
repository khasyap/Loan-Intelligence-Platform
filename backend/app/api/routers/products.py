from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.app.database.connection import get_db
from backend.app.models.entities import LoanProduct
from backend.app.schemas.pydantic_models import ProductSchema

router = APIRouter(prefix="/products", tags=["Loan Products"])

@router.get("", response_model=List[ProductSchema])
def list_products(db: Session = Depends(get_db)):
    """Retrieve all 4 configured loan products and their parameters."""
    return db.query(LoanProduct).all()

