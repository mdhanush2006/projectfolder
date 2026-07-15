from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import Domain, Exam, Subject, Topic, Question
from app.schemas import DomainResponse, ExamResponse, SubjectResponse
from sqlalchemy import func

router = APIRouter(prefix="/api/exams", tags=["Exams & Syllabus"])

@router.get("", response_model=List[DomainResponse])
def get_all_domains(db: Session = Depends(get_db)):
    return db.query(Domain).all()

@router.get("/{exam_code}/syllabus", response_model=List[SubjectResponse])
def get_exam_syllabus(exam_code: str, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.code == exam_code).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return db.query(Subject).filter(Subject.exam_id == exam.id).all()

@router.get("/pyq-analysis")
def get_pyq_analysis(
    exam_codes: List[str] = Query(None, alias="exams"),
    db: Session = Depends(get_db)
):
    # Base query for questions tagged as PYQ
    query = db.query(
        Question.id,
        Question.pyq_year,
        Question.pyq_exam,
        Question.difficulty,
        Question.weightage,
        Topic.name.label("topic_name"),
        Subject.name.label("subject_name"),
        Exam.code.label("exam_code")
    ).join(
        Topic, Question.topic_id == Topic.id
    ).join(
        Subject, Topic.subject_id == Subject.id
    ).join(
        Exam, Subject.exam_id == Exam.id
    ).filter(
        Question.pyq_year.isnot(None)
    )

    if exam_codes:
        query = query.filter(Exam.code.in_(exam_codes))

    pyq_questions = query.all()
    if not pyq_questions:
        return {
            "topic_trends": [],
            "difficulty_distribution": {},
            "year_shifts": {},
            "high_yield_ranking": []
        }

    # Process metrics
    import pandas as pd
    df = pd.DataFrame([
        {
            "year": q.pyq_year,
            "difficulty": q.difficulty,
            "weight": q.weightage,
            "topic": q.topic_name,
            "subject": q.subject_name,
            "exam": q.exam_code
        } for q in pyq_questions
    ])

    # 1. Topic-wise Trends (question count + total weightage)
    topic_trends = df.groupby(["subject", "topic"]).agg(
        frequency=("weight", "count"),
        total_weight=("weight", "sum")
    ).reset_index().to_dict(orient="records")

    # 2. Difficulty Distribution per Subject
    difficulty_dist = {}
    for sub in df["subject"].unique():
        sub_df = df[df["subject"] == sub]
        difficulty_dist[sub] = sub_df["difficulty"].value_counts().to_dict()

    # 3. Year-over-Year Shifts (number of PYQ questions per subject per year)
    year_shifts = {}
    years = sorted(df["year"].unique())
    for yr in years:
        yr_df = df[df["year"] == yr]
        year_shifts[int(yr)] = yr_df.groupby("subject")["weight"].sum().to_dict()

    # 4. High-yield topics ranking (sorted by weight)
    high_yield = df.groupby(["subject", "topic"])["weight"].sum().reset_index()
    high_yield = high_yield.sort_values(by="weight", ascending=False).head(10)
    high_yield_ranking = high_yield.to_dict(orient="records")

    return {
        "topic_trends": topic_trends,
        "difficulty_distribution": difficulty_dist,
        "year_shifts": year_shifts,
        "high_yield_ranking": high_yield_ranking
    }
