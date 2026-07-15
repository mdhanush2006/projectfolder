from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Exam, Subject, Topic, Question, TestAttempt, TestAttemptSection, TestAttemptAnswer
from app.schemas import TestSubmission, TestAttemptResponse, TestAttemptDetailResponse, QuestionResponse
from app.services.ai_services import detect_weak_topics, generate_study_plan
import random
from datetime import datetime

router = APIRouter(prefix="/api/tests", tags=["Tests & Practice"])

@router.get("/questions", response_model=List[QuestionResponse])
def get_practice_questions(
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    limit: int = 15,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Question)
    if topic_id:
        query = query.filter(Question.topic_id == topic_id)
    elif subject_id:
        query = query.join(Topic).filter(Topic.subject_id == subject_id)
    else:
        # Fallback to fetching questions inside user's target exams
        if current_user.target_exams:
            query = query.join(Topic).join(Subject).join(Exam).filter(Exam.code.in_(current_user.target_exams))
            
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
        
    questions = query.all()
    # Randomly sample questions to make it feel fresh
    if len(questions) > limit:
        questions = random.sample(questions, limit)
    return questions

@router.get("/mock/{exam_code}", response_model=Dict[str, Any])
def get_mock_test_template(
    exam_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exam = db.query(Exam).filter(Exam.code == exam_code).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
        
    # Get subjects in the exam
    subjects = db.query(Subject).filter(Subject.exam_id == exam.id).all()
    
    test_questions = []
    questions_per_subject = 10 # small but solid size for mock test queries
    
    for sub in subjects:
        # Get questions for this subject
        sub_questions = db.query(Question).join(Topic).filter(Topic.subject_id == sub.id).all()
        # Random sample
        sampled = random.sample(sub_questions, min(len(sub_questions), questions_per_subject))
        test_questions.extend(sampled)
        
    if not test_questions:
        raise HTTPException(status_code=400, detail="Not enough questions seeded to construct a mock test.")
        
    return {
        "exam_id": exam.id,
        "exam_name": exam.name,
        "duration_minutes": exam.duration_minutes,
        "total_marks": exam.total_marks,
        "negative_marking_factor": exam.negative_marking_factor,
        "questions": [QuestionResponse.model_validate(q) for q in test_questions]
    }

@router.post("/submit", response_model=TestAttemptResponse)
def submit_test(
    submission: TestSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve exam context if provided
    exam = None
    neg_marking = 0.25 # default 1/4th marking
    mark_per_question = 2.0 # default
    
    if submission.exam_id:
        exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
        if exam:
            neg_marking = exam.negative_marking_factor
            # Dynamically set mark base
            mark_per_question = exam.total_marks / max(1, len(submission.answers))

    # Evaluate answers
    correct = 0
    incorrect = 0
    skipped = 0
    score = 0.0
    max_score = 0.0

    # Build response structure for attempt answers
    attempt_answers = []
    subject_stats = {} # subject_id -> {correct, incorrect, skipped, score}

    for answer_in in submission.answers:
        question = db.query(Question).filter(Question.id == answer_in.question_id).first()
        if not question:
            continue
            
        topic = db.query(Topic).filter(Topic.id == question.topic_id).first()
        subject_id = topic.subject_id if topic else None
        
        if subject_id and subject_id not in subject_stats:
            subject_stats[subject_id] = {
                "correct": 0, 
                "incorrect": 0, 
                "skipped": 0, 
                "score": 0.0,
                "max_score": 0.0
            }

        max_score += mark_per_question
        if subject_id:
            subject_stats[subject_id]["max_score"] += mark_per_question

        is_correct = False
        selected_index = answer_in.selected_option_index
        
        if selected_index is None:
            skipped += 1
            if subject_id:
                subject_stats[subject_id]["skipped"] += 1
        elif selected_index == question.correct_option_index:
            correct += 1
            is_correct = True
            score += mark_per_question
            if subject_id:
                subject_stats[subject_id]["correct"] += 1
                subject_stats[subject_id]["score"] += mark_per_question
        else:
            incorrect += 1
            score -= (mark_per_question * neg_marking)
            if subject_id:
                subject_stats[subject_id]["incorrect"] += 1
                subject_stats[subject_id]["score"] -= (mark_per_question * neg_marking)

        # Record answer details
        attempt_answers.append(
            TestAttemptAnswer(
                question_id=question.id,
                selected_option_index=selected_index,
                is_correct=is_correct,
                time_spent_seconds=answer_in.time_spent_seconds
            )
        )

    # Make sure score doesn't fall below zero
    score = max(0.0, score)
    for sid in subject_stats:
        subject_stats[sid]["score"] = max(0.0, subject_stats[sid]["score"])

    # Create the test attempt record
    attempt = TestAttempt(
        user_id=current_user.id,
        exam_id=exam.id if exam else None,
        test_type=submission.test_type,
        score=score,
        max_score=max_score,
        correct_answers=correct,
        incorrect_answers=incorrect,
        skipped_answers=skipped,
        duration_seconds=exam.duration_minutes * 60 if exam else 0,
        time_spent_seconds=submission.time_spent_seconds,
        completed_at=datetime.utcnow()
    )

    db.add(attempt)
    db.commit() # Save attempt first to generate attempt.id

    # Add answers and sections to database
    for ans in attempt_answers:
        ans.test_attempt_id = attempt.id
        db.add(ans)

    for subject_id, stats in subject_stats.items():
        section = TestAttemptSection(
            test_attempt_id=attempt.id,
            subject_id=subject_id,
            score=stats["score"],
            max_score=stats["max_score"],
            correct=stats["correct"],
            incorrect=stats["incorrect"],
            skipped=stats["skipped"]
        )
        db.add(section)

    db.commit()
    db.refresh(attempt)

    # Trigger async/background-like AI services:
    # 1. Recalculate weak topics
    detect_weak_topics(db, current_user.id)
    
    # 2. Regenerate adaptive study plan if user has one
    if current_user.target_exams and current_user.daily_hours:
        generate_study_plan(
            db=db, 
            user_id=current_user.id, 
            target_exam_codes=current_user.target_exams, 
            daily_hours=current_user.daily_hours, 
            target_date_str=current_user.target_exam_date
        )

    return attempt
