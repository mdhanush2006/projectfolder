import os
import sys
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, get_db
from app.main import app
from app.models import User, Domain, Exam, Subject, Topic, Question

# Create testing session
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_examsphere.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestExamSphereBackend(unittest.TestCase):
    headers = {}

    @classmethod
    def setUpClass(cls):
        # Create database and seed
        Base.metadata.create_all(bind=engine)
        
        # Seed test database (we need to swap SessionLocal in seed to test)
        import app.seed as seed_mod
        original_session = seed_mod.SessionLocal
        seed_mod.SessionLocal = TestingSessionLocal
        seed_mod.seed_database()
        seed_mod.SessionLocal = original_session
        
        cls.client = TestClient(app)
        
        # Pre-register and login a user for all test cases
        register_payload = {
            "email": "test_aspirant@examsphere.com",
            "password": "securepassword123",
            "full_name": "Test Aspirant"
        }
        cls.client.post("/api/auth/register", json=register_payload)
        
        login_payload = {
            "email": "test_aspirant@examsphere.com",
            "password": "securepassword123"
        }
        res_login = cls.client.post("/api/auth/login", json=login_payload)
        token = res_login.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {token}"}

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if os.path.exists("./test_examsphere.db"):
            try:
                os.remove("./test_examsphere.db")
            except Exception as e:
                print("Failed to remove test DB file:", e)

    def test_health_check(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_auth_me_and_profile_update(self):
        # Me profile
        res_me = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.json()["email"], "test_aspirant@examsphere.com")

        # Update profile (select target exam, which also triggers study plan generation)
        profile_update = {
            "target_exams": ["ssc-cgl"],
            "target_domain": "staff selection commission",
            "daily_hours": 4.0,
            "target_exam_date": "2026-12-31"
        }
        res_update = self.client.put("/api/auth/profile", json=profile_update, headers=self.headers)
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["daily_hours"], 4.0)

    def test_syllabus_and_pyq(self):
        # Get domains
        res_domains = self.client.get("/api/exams")
        self.assertEqual(res_domains.status_code, 200)
        self.assertTrue(len(res_domains.json()) > 0)
        
        # Get CGL Syllabus
        res_syllabus = self.client.get("/api/exams/ssc-cgl/syllabus")
        self.assertEqual(res_syllabus.status_code, 200)
        self.assertTrue(len(res_syllabus.json()) > 0)

        # Get PYQ Analysis
        res_pyq = self.client.get("/api/exams/pyq-analysis?exams=ssc-cgl")
        self.assertEqual(res_pyq.status_code, 200)
        self.assertIn("high_yield_ranking", res_pyq.json())

    def test_mock_test_and_submit(self):
        # Get mock template from the correct route
        res_mock = self.client.get("/api/tests/mock/ssc-cgl", headers=self.headers)
        self.assertEqual(res_mock.status_code, 200)
        questions = res_mock.json()["questions"]
        self.assertTrue(len(questions) > 0)

        # Submit mock attempt
        answers = []
        for q in questions:
            answers.append({
                "question_id": q["id"],
                "selected_option_index": q["correct_option_index"], # simulate 100% correct answers
                "time_spent_seconds": 15
            })
            
        submit_payload = {
            "exam_id": res_mock.json()["exam_id"],
            "test_type": "mock",
            "answers": answers,
            "time_spent_seconds": len(questions) * 15
        }
        
        res_submit = self.client.post("/api/tests/submit", json=submit_payload, headers=self.headers)
        self.assertEqual(res_submit.status_code, 200)
        self.assertEqual(res_submit.json()["correct_answers"], len(questions))

    def test_ai_planner_and_chat(self):
        # We need to make sure the user profile has target exams set
        # This was set in test_auth_me_and_profile_update, but tests are alphabetical,
        # so test_ai_planner_and_chat might run before it. Let's make sure it's set here too
        profile_update = {
            "target_exams": ["ssc-cgl"],
            "target_domain": "staff selection commission",
            "daily_hours": 4.0,
            "target_exam_date": "2026-12-31"
        }
        self.client.put("/api/auth/profile", json=profile_update, headers=self.headers)

        # Get Study Plan
        res_plan = self.client.get("/api/ai/study-plan", headers=self.headers)
        self.assertEqual(res_plan.status_code, 200)
        self.assertIn("schedule", res_plan.json()["plan_data"])

        # Query priority topics
        res_priority = self.client.get("/api/ai/priority-topics", headers=self.headers)
        self.assertEqual(res_priority.status_code, 200)
        self.assertTrue(len(res_priority.json()) > 0)

        # Query chat mentor (mock response test)
        chat_payload = {
            "question": "How do I calculate percentages quickly?",
            "topic_id": None
        }
        res_chat = self.client.post("/api/ai/chat", json=chat_payload, headers=self.headers)
        self.assertEqual(res_chat.status_code, 200)
        self.assertIn("answer", res_chat.json())
        self.assertIn("practice_question", res_chat.json())

if __name__ == "__main__":
    unittest.main()
