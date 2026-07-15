from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth import get_current_user
from app.models import User, TestAttempt
from app.schemas import TestAttemptResponse, TestAttemptDetailResponse

router = APIRouter(prefix="/api/results", tags=["Test Results"])

@router.get("", response_model=List[TestAttemptResponse])
def get_user_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempts = db.query(TestAttempt).filter(
        TestAttempt.user_id == current_user.id
    ).order_by(TestAttempt.completed_at.desc()).all()
    
    # Map exam names dynamically before returning
    res_list = []
    for a in attempts:
        exam_name = a.exam.name if a.exam else "Topic Practice Session"
        # We can construct Pydantic manually or let it read from properties
        setattr(a, "exam_name", exam_name)
        res_list.append(a)
    return res_list

@router.get("/{attempt_id}", response_model=TestAttemptDetailResponse)
def get_result_detail(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.user_id == current_user.id
    ).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Result attempt not found")
        
    exam_name = attempt.exam.name if attempt.exam else "Topic Practice Session"
    setattr(attempt, "exam_name", exam_name)

    # Attach section names dynamically
    for s in attempt.sections:
        setattr(s, "subject_name", s.subject.name)

    return attempt
