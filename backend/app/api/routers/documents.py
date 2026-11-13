from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import datetime

from backend.app.database.connection import get_db
from backend.app.models.entities import Document, DocumentVerificationHistory, LoanApplication
from backend.app.services.security import require_role

router = APIRouter(prefix="/documents", tags=["Document Management"])

class DocumentVerifyRequest(BaseModel):
    verification_status: str  # VERIFIED, REJECTED, EXPIRED
    reason: Optional[str] = None
    reviewer_id: Optional[str] = "OPERATIONS_DESK"

@router.get("", response_model=List[Dict[str, Any]])
def list_documents(
    application_id: Optional[str] = None,
    verification_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Query submitted verification documents with application and status filters."""
    q = db.query(Document)
    if application_id:
        q = q.filter(Document.application_id == application_id)
    if verification_status:
        q = q.filter(Document.verification_status == verification_status)
    docs = q.limit(100).all()
    return [
        {
            "document_id": d.document_id,
            "application_id": d.application_id,
            "document_type": d.document_type,
            "submission_status": d.submission_status,
            "verification_status": d.verification_status,
            "rejection_reason": d.rejection_reason,
            "document_reference": d.document_reference
        } for d in docs
    ]

@router.post("/{document_id}/verify", response_model=Dict[str, Any])
def verify_document(
    document_id: str,
    payload: DocumentVerifyRequest,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role(["OPERATIONS_ANALYST", "ADMIN"]))
):
    """Operations Analyst or Admin updates document verification status and logs history."""
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    prev_status = doc.verification_status
    doc.verification_status = payload.verification_status
    doc.rejection_reason = payload.reason
    doc.verified_at = datetime.datetime.now(datetime.timezone.utc)

    # Log history
    hist_count = db.query(DocumentVerificationHistory).count()
    hist = DocumentVerificationHistory(
        history_id=f"DVH-{hist_count + 1:06d}",
        document_id=document_id,
        previous_status=prev_status,
        new_status=payload.verification_status,
        verified_at=doc.verified_at,
        verified_by=user.get("name", payload.reviewer_id),
        reason=payload.reason
    )
    db.add(hist)
    db.commit()

    return {
        "document_id": doc.document_id,
        "previous_status": prev_status,
        "new_status": doc.verification_status,
        "verified_by": user.get("name")
    }

