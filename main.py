import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import ContentMaterial
from app.routers import auth, exams, tests, results, ai, admin, quizzes

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ExamSphere AI API",
    description="Full-stack AI-powered competitive exam preparation mentor engine",
    version="1.0.0"
)

# Configure CORS for Vite React client
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "https://examsphere-ai.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(exams.router)
app.include_router(tests.router)
app.include_router(results.router)
app.include_router(ai.router)
app.include_router(admin.router)
app.include_router(admin.student_reports_router)
app.include_router(admin.student_content_router)
app.include_router(quizzes.router)

# Serve uploaded files statically
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    content_type: str = Form("Doc"),
    category: str = Form("General"),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    """Upload a file (PDF, DOC, PPT, etc.) and create a content record."""
    # Generate unique filename to avoid collisions
    ext = os.path.splitext(file.filename or "file")[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save the file to disk
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_url = f"/uploads/{unique_name}"

    # Create database record
    db_content = ContentMaterial(
        title=title,
        content_type=content_type,
        file_url=file_url,
        description=description,
        is_published=True,
        category=category,
        subject_id=None,
        topic_id=None,
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)

    return {
        "id": db_content.id,
        "title": db_content.title,
        "content_type": db_content.content_type,
        "file_url": db_content.file_url,
        "category": db_content.category,
        "created_at": db_content.created_at.isoformat() if db_content.created_at else None,
    }


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "ExamSphere AI Core Engine",
        "version": "1.0.0"
    }
