from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.auth import get_current_user
from app.models import User, StudyPlan, WeakTopic
from app.schemas import WeakTopicResponse, StudyPlanResponse, PriorityTopicResponse, ChatQuery, ChatResponse
from app.services.ai_services import (
    detect_weak_topics,
    get_priority_topics,
    generate_study_plan,
    ask_chat_mentor
)

router = APIRouter(prefix="/api/ai", tags=["AI Copilot & Mentor"])

@router.get("/weak-topics", response_model=List[WeakTopicResponse])
def get_user_weak_topics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    weak_db = db.query(WeakTopic).filter(WeakTopic.user_id == current_user.id).all()
    
    # If empty, try to detect them (first time evaluation)
    if not weak_db:
        weak_db = detect_weak_topics(db, current_user.id)

    response = []
    for w in weak_db:
        response.append(WeakTopicResponse(
            topic_id=w.topic_id,
            topic_name=w.topic.name,
            subject_name=w.topic.subject.name,
            accuracy_rate=w.accuracy_rate,
            avg_time_seconds=w.avg_time_seconds,
            weight=w.weight
        ))
    return response

@router.get("/study-plan", response_model=StudyPlanResponse)
def get_user_study_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    
    # Auto-generate if no plan exists but target exams are set
    if not plan and current_user.target_exams:
        plan_data = generate_study_plan(
            db=db,
            user_id=current_user.id,
            target_exam_codes=current_user.target_exams,
            daily_hours=current_user.daily_hours,
            target_date_str=current_user.target_exam_date
        )
        plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
        
    if not plan:
        raise HTTPException(
            status_code=400, 
            detail="Study plan not generated. Setup target exams in onboarding/profile first."
        )
    return plan

@router.post("/study-plan/regenerate", response_model=StudyPlanResponse)
def regenerate_user_study_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.target_exams:
        raise HTTPException(
            status_code=400, 
            detail="Cannot generate plan. Target exams are not configured."
        )
    generate_study_plan(
        db=db,
        user_id=current_user.id,
        target_exam_codes=current_user.target_exams,
        daily_hours=current_user.daily_hours,
        target_date_str=current_user.target_exam_date
    )
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    return plan

@router.get("/priority-topics", response_model=List[PriorityTopicResponse])
def get_user_priority_topics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.target_exams:
        return []
    priorities = get_priority_topics(db, current_user.id, current_user.target_exams)
    return [PriorityTopicResponse(**p) for p in priorities]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_mentor(
    query: ChatQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Set context if topic_id is passed
    topic_name = None
    if query.topic_id:
        topic_name = db.query(WeakTopic.topic.name).join(WeakTopic).filter(WeakTopic.topic_id == query.topic_id).scalar()
        
    explanation_context = ""
    if query.context_test_id:
        # User is asking about a specific test question
        explanation_context = f"Attempting explanation for doubt raised in Test Attempt ID: {query.context_test_id}"
        
    res = await ask_chat_mentor(
        question=query.question, 
        topic_name=topic_name, 
        explanation_context=explanation_context
    )
    return res
