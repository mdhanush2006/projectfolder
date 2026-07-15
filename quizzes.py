from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Quiz, QuizQuestion, QuizAttempt, QuizAttemptAnswer
from app.schemas import QuizResponse, QuizDetailResponse, QuizSubmission, QuizAttemptResponse, QuizAttemptDetailResponse
from datetime import datetime

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])

@router.get("", response_model=List[QuizResponse])
def get_published_quizzes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Quiz).filter(Quiz.status == "published").order_by(Quiz.created_at.desc()).all()

@router.get("/{quiz_id}", response_model=QuizDetailResponse)
def get_quiz_details(quiz_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.status == "published").first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found or not published")
    return quiz

@router.post("/{quiz_id}/submit", response_model=QuizAttemptResponse)
def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.status == "published").first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    correct = 0
    incorrect = 0
    skipped = 0
    score = 0.0
    max_score = 0.0

    # Load questions to map answers
    questions = {q.id: q for q in quiz.questions}
    
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=current_user.id,
        time_spent_seconds=submission.time_spent_seconds,
        completed_at=datetime.utcnow()
    )
    db.add(attempt)
    db.flush()  # get attempt.id

    for ans in submission.answers:
        q = questions.get(ans.question_id)
        if not q:
            continue
        
        max_score += q.marks
        is_corr = False
        
        if not ans.selected_option:
            skipped += 1
        else:
            # Compare character values
            is_corr = (ans.selected_option.upper() == q.correct_answer.upper())
            if is_corr:
                correct += 1
                score += q.marks
            else:
                incorrect += 1
                score -= q.negative_marks

        attempt_ans = QuizAttemptAnswer(
            quiz_attempt_id=attempt.id,
            question_id=ans.question_id,
            selected_option=ans.selected_option,
            is_correct=is_corr,
            time_spent_seconds=ans.time_spent_seconds
        )
        db.add(attempt_ans)

    attempt.score = round(score, 2)
    attempt.max_score = round(max_score, 2)
    attempt.correct_answers = correct
    attempt.incorrect_answers = incorrect
    attempt.skipped_answers = skipped

    db.commit()
    db.refresh(attempt)
    return attempt

@router.get("/attempts/my", response_model=List[QuizAttemptResponse])
def get_my_attempts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).order_by(QuizAttempt.completed_at.desc()).all()

@router.get("/attempts/{attempt_id}", response_model=QuizAttemptDetailResponse)
def get_attempt_details(attempt_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    return attempt
