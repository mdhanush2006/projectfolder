from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import pandas as pd
import numpy as np
import httpx
from typing import List, Dict, Any, Optional
from app.models import TestAttempt, TestAttemptAnswer, Question, Topic, Subject, WeakTopic, StudyPlan, Exam
from app.config import settings

# 1. WEAK TOPIC DETECTOR
def detect_weak_topics(db: Session, user_id: int) -> List[WeakTopic]:
    # Fetch all answers submitted by this user
    answers = db.query(
        TestAttemptAnswer.question_id,
        TestAttemptAnswer.selected_option_index,
        TestAttemptAnswer.is_correct,
        TestAttemptAnswer.time_spent_seconds,
        Question.topic_id
    ).join(
        TestAttempt, TestAttemptAnswer.test_attempt_id == TestAttempt.id
    ).join(
        Question, TestAttemptAnswer.question_id == Question.id
    ).filter(
        TestAttempt.user_id == user_id
    ).all()

    if not answers:
        return []

    # Load into Pandas DataFrame for easy analysis
    df = pd.DataFrame([
        {
            "topic_id": a.topic_id,
            "is_correct": a.is_correct,
            "time_spent": a.time_spent_seconds
        } for a in answers
    ])

    # Group by topic_id and compute accuracy and average time
    grouped = df.groupby("topic_id").agg(
        total_attempts=("is_correct", "count"),
        correct_attempts=("is_correct", "sum"),
        avg_time=("time_spent", "mean")
    ).reset_index()

    grouped["accuracy"] = grouped["correct_attempts"] / grouped["total_attempts"]

    # Calculate a weakness weight score:
    # High weight = high weakness (low accuracy + high time spent)
    # Formula: weight = (1 - accuracy) * 7.0 + (avg_time / 45.0) * 3.0
    # Limit max weight to 10.0
    grouped["weight"] = (1.0 - grouped["accuracy"]) * 7.0 + (grouped["avg_time"] / 45.0) * 3.0
    grouped["weight"] = grouped["weight"].clip(upper=10.0)

    # Filter out topics where user has good accuracy (e.g. > 85%) and low time spent
    # But keep topics where accuracy is low (< 75%) or time spent is high
    weak_df = grouped[
        (grouped["accuracy"] < 0.75) | 
        (grouped["weight"] > 4.5)
    ]

    # Save to database
    # Delete old weak topics for this user first
    db.query(WeakTopic).filter(WeakTopic.user_id == user_id).delete()

    weak_topics_list = []
    for _, row in weak_df.iterrows():
        weak_topic = WeakTopic(
            user_id=user_id,
            topic_id=int(row["topic_id"]),
            accuracy_rate=float(row["accuracy"]),
            avg_time_seconds=float(row["avg_time"]),
            weight=float(row["weight"]),
            last_evaluated=datetime.utcnow()
        )
        db.add(weak_topic)
        weak_topics_list.append(weak_topic)

    db.commit()
    return weak_topics_list


# 2. PRIORITY CORRECTION ENGINE
def get_priority_topics(db: Session, user_id: int, target_exam_codes: List[str]) -> List[Dict[str, Any]]:
    # Get all subjects/topics in the target exams
    topics_query = db.query(
        Topic.id.label("topic_id"),
        Topic.name.label("topic_name"),
        Subject.name.label("subject_name")
    ).join(
        Subject, Topic.subject_id == Subject.id
    ).join(
        Exam, Subject.exam_id == Exam.id
    ).filter(
        Exam.code.in_(target_exam_codes)
    )
    
    all_topics = topics_query.all()
    if not all_topics:
        return []

    # Get user's weak topics evaluation
    weak_topics_db = db.query(WeakTopic).filter(WeakTopic.user_id == user_id).all()
    weak_map = {w.topic_id: w for w in weak_topics_db}

    # Retrieve PYQ frequency / weightage for each topic
    # Let's aggregate question weights from questions tagged as PYQs
    pyq_freq = db.query(
        Question.topic_id,
        func.avg(Question.weightage).label("avg_weight"),
        func.count(Question.id).label("q_count")
    ).filter(
        Question.pyq_year.isnot(None)
    ).group_by(Question.topic_id).all()
    
    pyq_map = {p.topic_id: (float(p.avg_weight or 1.0) * float(p.q_count)) for p in pyq_freq}

    priority_list = []
    for t in all_topics:
        tid = t.topic_id
        # PYQ frequency factor: defaults to 1.0 (average frequency) if no question data
        freq = pyq_map.get(tid, 1.0)
        
        # User accuracy: 1.0 (perfect) if not weak, else retrieve from weak map.
        # If never attempted, assume 0.5 (neutral)
        is_weak = tid in weak_map
        if is_weak:
            acc = weak_map[tid].accuracy_rate
            weakness_score = 1.0 - acc
        else:
            # Check if user has attempted this topic at all
            attempts_count = db.query(func.count(TestAttemptAnswer.id)).join(
                Question, TestAttemptAnswer.question_id == Question.id
            ).join(
                TestAttempt, TestAttemptAnswer.test_attempt_id == TestAttempt.id
            ).filter(
                TestAttempt.user_id == user_id,
                Question.topic_id == tid
            ).scalar()
            
            if attempts_count == 0:
                weakness_score = 0.5 # unattempted, medium priority
            else:
                weakness_score = 0.1 # attempted and strong, low priority

        # Priority calculation: weakness intersect with pyq frequency
        priority_score = weakness_score * freq

        priority_list.append({
            "topic_id": tid,
            "topic_name": t.topic_name,
            "subject_name": t.subject_name,
            "accuracy_rate": float(weak_map[tid].accuracy_rate) if is_weak else (1.0 if weakness_score == 0.1 else 0.5),
            "pyq_frequency": float(freq),
            "priority_score": float(priority_score)
        })

    # Sort descending by priority score
    priority_list.sort(key=lambda x: x["priority_score"], reverse=True)
    return priority_list


# 3. ADAPTIVE STUDY PLANNER
def generate_study_plan(db: Session, user_id: int, target_exam_codes: List[str], daily_hours: float, target_date_str: Optional[str]) -> Dict[str, Any]:
    # Calculate days left
    days_left = 30 # default
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
            delta = target_date - datetime.utcnow()
            if delta.days > 0:
                days_left = min(delta.days, 90) # cap at 90 days for preview
        except ValueError:
            pass

    # Fetch prioritized topics
    priorities = get_priority_topics(db, user_id, target_exam_codes)
    if not priorities:
        # Fallback to fetching some topics from target exams
        db_topics = db.query(
            Topic.id, Topic.name, Subject.name
        ).join(
            Subject, Topic.subject_id == Subject.id
        ).join(
            Exam, Subject.exam_id == Exam.id
        ).filter(
            Exam.code.in_(target_exam_codes)
        ).limit(10).all()
        
        priorities = [{
            "topic_id": t.id,
            "topic_name": t.name,
            "subject_name": t.name,
            "accuracy_rate": 0.5,
            "pyq_frequency": 1.0,
            "priority_score": 0.5
        } for t in db_topics]

    # Generate daily schedule
    schedule = {}
    topic_index = 0
    total_topics = len(priorities)

    # Guard: if no topics found, return empty schedule
    if total_topics == 0:
        return {"schedule": {}, "message": "No topics found for selected exams. Please complete onboarding."}

    for day in range(1, days_left + 1):
        if topic_index >= total_topics:
            topic_index = 0  # loop back if needed

        # Select 1 or 2 topics for the day based on study hours
        topics_today = []
        if daily_hours >= 4.0 and total_topics > 1:
            topics_today = [priorities[topic_index], priorities[(topic_index + 1) % total_topics]]
            topic_index = (topic_index + 2) % total_topics
        else:
            topics_today = [priorities[topic_index]]
            topic_index = (topic_index + 1) % total_topics


        tasks = []
        for t in topics_today:
            # Custom task prompts based on priority
            is_high_priority = t["priority_score"] > 0.6
            if is_high_priority:
                tasks.append({
                    "type": "Concept Learning & Weakness Review",
                    "topic_id": t["topic_id"],
                    "topic_name": t["topic_name"],
                    "subject_name": t["subject_name"],
                    "description": f"Focus on core concepts. Go through notes or ask AI Mentor about {t['topic_name']}.",
                    "duration_mins": int(daily_hours * 60 * 0.4)
                })
                tasks.append({
                    "type": "Practice Set",
                    "topic_id": t["topic_id"],
                    "topic_name": t["topic_name"],
                    "subject_name": t["subject_name"],
                    "description": f"Solve at least 20 medium/hard practice questions on {t['topic_name']}.",
                    "duration_mins": int(daily_hours * 60 * 0.6)
                })
            else:
                tasks.append({
                    "type": "Formulas & Quick Revision",
                    "topic_id": t["topic_id"],
                    "topic_name": t["topic_name"],
                    "subject_name": t["subject_name"],
                    "description": f"Revise key summaries and formulas for {t['topic_name']}.",
                    "duration_mins": int(daily_hours * 60 * 0.3)
                })
                tasks.append({
                    "type": "Speed Practice",
                    "topic_id": t["topic_id"],
                    "topic_name": t["topic_name"],
                    "subject_name": t["subject_name"],
                    "description": f"Take a quick 10-question practice test on {t['topic_name']} with timer constraint.",
                    "duration_mins": int(daily_hours * 60 * 0.7)
                })

        # Add weekly mock test reminders
        if day % 7 == 0:
            tasks.append({
                "type": "Full-Length Mock Simulation",
                "topic_id": None,
                "topic_name": "Full Mock Test",
                "subject_name": "Multi-Subject",
                "description": f"Simulate a real exam environment for one of your target exams: {', '.join(target_exam_codes).upper()}.",
                "duration_mins": 90
            })

        schedule[f"Day {day}"] = {
            "topics": [t["topic_name"] for t in topics_today],
            "tasks": tasks
        }

    plan_data = {
        "target_exams": target_exam_codes,
        "daily_hours": daily_hours,
        "total_days": days_left,
        "schedule": schedule
    }

    # Save to db
    # Delete old plans
    db.query(StudyPlan).filter(StudyPlan.user_id == user_id).delete()
    
    study_plan = StudyPlan(
        user_id=user_id,
        plan_data=plan_data,
        generated_at=datetime.utcnow()
    )
    db.add(study_plan)
    db.commit()

    return plan_data


# 4. CHAT MENTOR ENGINE
async def ask_chat_mentor(question: str, topic_name: Optional[str] = None, explanation_context: Optional[str] = None) -> Dict[str, Any]:
    prompt = f"""You are 'ExamSphere AI Mentor', a highly supportive, expert personal tutor for aspirants preparing for competitive government exams like SSC, Banking, Railways, and UPSC.
Provide clear, step-by-step conceptual explanations, examples, and strategies.
Question/Topic: {question}
Topic Name: {topic_name or 'General Prep'}
Context: {explanation_context or 'None'}

Provide your response in JSON format matching this schema:
{{
  "answer": "Your detailed explanation in markdown format...",
  "practice_question": "A mock practice question related to this query (optional)...",
  "options": ["Option A", "Option B", "Option C", "Option D"] (optional),
  "correct_option_index": 0-3 (optional),
  "explanation": "Brief explanation of the practice question (optional)"
}}
"""
    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=payload, timeout=20.0)
                if res.status_code == 200:
                    data = res.json()
                    text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                    import json
                    return json.loads(text_content)
        except Exception as e:
            # Logging error internally, falling back to mock response below
            print("Gemini API call failed, falling back to Mock:", str(e))
            pass

    # Mock response generator (highly responsive and functional fallback)
    question_lower = question.lower()
    
    # Check if they are asking about standard quantitative/reasoning/general topics
    if "percent" in question_lower or "ratio" in question_lower or "math" in question_lower:
        return {
            "answer": "### Concept: Understanding Percentages\n\nPercentages represent fractions with a denominator of 100. In competitive exams, mastering **fraction-to-percentage conversions** is crucial for speed.\n\n*   \\(1/2 = 50\\%\\)\n*   \\(1/3 = 33.33\\%\\)\n*   \\(1/4 = 25\\%\\)\n*   \\(1/8 = 12.5\\%\\)\n\n**Exam Shortcut:** To increase a number by \\(x\\%\\), multiply it by \\(1 + x/100\\). For example, to increase $120$ by $25\\%$, multiply by $1.25$: \n\\[120 \\times 1.25 = 150\\]",
            "practice_question": "If the price of petrol increases by 25%, by how much percent must a motorist reduce his consumption so as not to increase his expenditure?",
            "options": ["20%", "25%", "16.67%", "33.33%"],
            "correct_option_index": 0,
            "explanation": "Let expenditure be \\(E = P \\times C\\). New price \\(P' = 1.25 P\\). To keep expenditure same: \\(1.25 P \\times C' = P \\times C \\implies C' = C / 1.25 = 0.8 C\\). Thus, consumption is reduced by 20%."
        }
    elif "syllogism" in question_lower or "reasoning" in question_lower or "logic" in question_lower:
        return {
            "answer": "### Concept: Syllogism Rules\n\nSyllogisms test deductive reasoning. Use **Venn Diagrams** to analyze relations between categories: \n\n1.  **All A are B:** Circle A is fully inside Circle B.\n2.  **Some A are B:** Circle A and B overlap.\n3.  **No A are B:** Circle A and B are completely separate.\n\n*Rule of thumb:* Never assume facts outside the given statements. Focus strictly on what is definitely true in all possible diagrams.",
            "practice_question": "Statements: (I) All singers are dancers. (II) Some dancers are actors. \nConclusions: (I) Some singers are actors. (II) Some actors are singers.",
            "options": ["Only conclusion I follows", "Only conclusion II follows", "Either I or II follows", "Neither I nor II follows"],
            "correct_option_index": 3,
            "explanation": "Since Circle Singer is inside Dancer, and Dancer overlaps with Actor, Singer may or may not overlap with Actor. No definite relationship exists, so neither follows."
        }
    elif "history" in question_lower or "polity" in question_lower or "current" in question_lower or "gk" in question_lower or "general awareness" in question_lower:
        return {
            "answer": "### Concept: Key Indian Constitution Articles\n\nFor government exams (SSC, UPSC, State PSC), knowing fundamental constitutional articles is highly yield:\n\n*   **Article 14:** Equality before law\n*   **Article 21:** Protection of life and personal liberty\n*   **Article 32:** Right to constitutional remedies (often called the 'Heart and Soul' of the Constitution by Dr. B.R. Ambedkar)\n*   **Article 360:** Provisions as to financial emergency",
            "practice_question": "Which Article of the Indian Constitution empowers the Supreme Court to issue writs for enforcement of Fundamental Rights?",
            "options": ["Article 32", "Article 226", "Article 143", "Article 51A"],
            "correct_option_index": 0,
            "explanation": "Article 32 confers the right to move the Supreme Court for writ remedies, while Article 226 gives high courts similar powers."
        }
    else:
        # Default smart response
        return {
            "answer": f"### Preparation Strategy for: {topic_name or 'ExamSphere AI'}\n\nTo master competitive government exams, maintain a balanced schedule of **concept learning**, **topic tests**, and **full mock simulations**.\n\n1.  **Identify High-Yield Topics:** Focus on topics that repeat most often in Previous Year Papers.\n2.  **Analyze Weaknesses:** Use your ExamSphere AI weak topics list to schedule remedial practice.\n3.  **Speed & Accuracy:** Track your time-per-question during topic practice to avoid exam-day pressure.",
            "practice_question": "Which of the following is the most efficient way to improve test speed in competitive exams?",
            "options": [
                "Attempting hard questions first",
                "Skipping long questions on first pass and using key formula shortcuts",
                "Reading the complete question paper before answering",
                "Spending equal time on all sections"
            ],
            "correct_option_index": 1,
            "explanation": "By filtering questions in rounds (doing easy/short ones first and using shortcuts), you maximize score efficiency within the time limit."
        }
