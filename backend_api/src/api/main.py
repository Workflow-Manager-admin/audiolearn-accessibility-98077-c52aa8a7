"""
FastAPI backend for an accessible English learning app with:
– English content (words, sentences, paragraphs)
– User management/preferences (including TTS speed & font size)
– Multilingual support (language fields)
– TTS endpoints & DB check
– Quiz system & result tracking
– Favorites & daily suggestions
– Voice command API scaffold
– Health check/system info

This backend uses SQLite and exposes a RESTful API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import random
import sqlite3


# -- Database utility setup (simple for demonstration, not production scale!) --
DB_PATH = "audiolearn_accessibility.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # Create tables if they don't exist
    conn = get_db()
    c = conn.cursor()

    # User table (preferences, favorites, etc.)
    c.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        preferred_font_size INTEGER DEFAULT 18,
        preferred_tts_speed REAL DEFAULT 1.0,
        preferred_language TEXT DEFAULT 'en'
    )
    """)
    # Learning content tables
    c.execute("""
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, -- 'word' | 'sentence' | 'paragraph'
        text TEXT NOT NULL,
        language TEXT NOT NULL, -- 'en', 'ta', 'hi'
        translation TEXT,
        audio_url TEXT
    )
    """)
    # Favorites table
    c.execute("""
    CREATE TABLE IF NOT EXISTS favorite (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (content_id) REFERENCES content(id)
    )
    """)
    # Quiz table
    c.execute("""
    CREATE TABLE IF NOT EXISTS quiz (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_id INTEGER,
        question TEXT,
        correct_answer TEXT,
        distractors TEXT,
        language TEXT,
        FOREIGN KEY (content_id) REFERENCES content(id)
    )
    """)
    # Quiz results
    c.execute("""
    CREATE TABLE IF NOT EXISTS quiz_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        quiz_id INTEGER,
        score INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (quiz_id) REFERENCES quiz(id)
    )
    """)
    conn.commit()
    conn.close()


init_db()


# -- FastAPI setup --
app = FastAPI(
    title="AudioLearn Accessible English Backend",
    description=(
        "API for accessible English learning platform (with TTS, multilingual, quiz, favorites, and more)"
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "content", "description": "English learning content (words, sentences, paragraphs)"},
        {"name": "user", "description": "User management and preferences"},
        {"name": "tts", "description": "Text-to-speech endpoints"},
        {"name": "quiz", "description": "Quiz features and result tracking"},
        {"name": "favorites", "description": "Favorites and daily suggestions"},
        {"name": "voice", "description": "Voice command interface support"},
        {"name": "health", "description": "System health and DB checks"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------- SCHEMAS ----------------------- #

class UserCreate(BaseModel):
    username: str = Field(..., description="Unique username.")
    preferred_font_size: Optional[int] = Field(
        18, description="Font size preference"
    )
    preferred_tts_speed: Optional[float] = Field(
        1.0, description="TTS speech speed (1.0=normal)"
    )
    preferred_language: Optional[str] = Field(
        "en", description="Language: 'en', 'ta', 'hi'."
    )


class UserOut(UserCreate):
    id: int


class ContentBase(BaseModel):
    type: str = Field(
        ..., description="Type: 'word', 'sentence', 'paragraph'"
    )
    text: str = Field(..., description="Main content text")
    language: str = Field(..., description="Language code, e.g., 'en', 'ta', 'hi'")
    translation: Optional[str] = Field(
        None,
        description="Translation in another language"
    )
    audio_url: Optional[str] = Field(
        None,
        description=(
            "URL to pre-generated TTS or audio"
        )
    )


class ContentOut(ContentBase):
    id: int


class FavoriteOut(BaseModel):
    id: int
    user_id: int
    content_id: int


class QuizCreate(BaseModel):
    content_id: int
    question: str
    correct_answer: str
    distractors: List[str]
    language: str = Field(..., description="Language for the quiz")


class QuizOut(BaseModel):
    id: int
    content_id: int
    question: str
    correct_answer: str
    distractors: List[str]
    language: str


class QuizResultCreate(BaseModel):
    user_id: int
    quiz_id: int
    score: int


class QuizResultOut(QuizResultCreate):
    id: int
    timestamp: str


class VoiceCommandRequest(BaseModel):
    command: str = Field(
        ..., description="Raw spoken command text or intent name"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="Context object")


class TTSRequest(BaseModel):
    content_id: int


class TTSBatchRequest(BaseModel):
    content_ids: List[int]


class TTSTestResponse(BaseModel):
    text: str
    tts_audio: Optional[str] = Field(
        None, description="Stubbed: normally a URL or binary/audio blob"
    )


class DailySuggestionOut(BaseModel):
    suggestion: ContentOut


# --------------------- ENDPOINTS --------------------- #

# HEALTH CHECK
@app.get("/", tags=["health"], summary="System health check")
def health_check():
    """Check API backend is running."""
    return {"status": "Healthy"}


# ------------------ User Endpoints ------------------- #

# PUBLIC_INTERFACE
@app.post(
    "/users/", response_model=UserOut, tags=["user"], summary="Register new user"
)
def create_user(user: UserCreate):
    """Register a new user with language and preference fields."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO user (username, preferred_font_size, preferred_tts_speed, preferred_language) "
            "VALUES (?, ?, ?, ?)",
            (
                user.username,
                user.preferred_font_size,
                user.preferred_tts_speed,
                user.preferred_language,
            ),
        )
        user_id = c.lastrowid
        conn.commit()
        return {**user.dict(), "id": user_id}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.get(
    "/users/{user_id}", response_model=UserOut, tags=["user"], summary="Get user info"
)
def get_user(user_id: int):
    """Fetch user info and preferences."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM user WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


# PUBLIC_INTERFACE
@app.put(
    "/users/{user_id}/preferences",
    response_model=UserOut,
    tags=["user"],
    summary="Update user preferences"
)
def update_user_preferences(user_id: int, update: UserCreate):
    """Update preferences and language for a user."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE user SET preferred_font_size=?, preferred_tts_speed=?, preferred_language=? WHERE id=?",
        (
            update.preferred_font_size,
            update.preferred_tts_speed,
            update.preferred_language,
            user_id,
        ),
    )
    conn.commit()
    c.execute("SELECT * FROM user WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


# ------------------ Content Endpoints ------------------- #

# PUBLIC_INTERFACE
@app.post(
    "/content/",
    response_model=ContentOut,
    tags=["content"],
    summary="Add new learning content"
)
def add_content(content: ContentBase):
    """Add word/sentence/paragraph content (with optional translation)."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO content (type, text, language, translation, audio_url) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            content.type,
            content.text,
            content.language,
            content.translation,
            content.audio_url
        )
    )
    content_id = c.lastrowid
    conn.commit()
    conn.close()
    return {**content.dict(), "id": content_id}


# PUBLIC_INTERFACE
@app.get(
    "/content/",
    response_model=List[ContentOut],
    tags=["content"],
    summary="List content"
)
def list_content(
    type: Optional[str] = None,
    language: Optional[str] = None
):
    """List content (optionally filter by type and/or language)."""
    conn = get_db()
    c = conn.cursor()
    base = "SELECT * FROM content WHERE 1=1"
    filters = []
    params = []
    if type:
        filters.append("type=?")
        params.append(type)
    if language:
        filters.append("language=?")
        params.append(language)
    sql = base + (" AND " + " AND ".join(filters) if filters else "")
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# PUBLIC_INTERFACE
@app.get(
    "/content/{content_id}",
    response_model=ContentOut,
    tags=["content"],
    summary="Get content by ID"
)
def get_content(content_id: int):
    """Fetch one word/sentence/paragraph by ID"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM content WHERE id=?", (content_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return dict(row)


# ------------------ Favorites & Daily Suggestion ------------------- #

# PUBLIC_INTERFACE
@app.post(
    "/favorites/",
    response_model=FavoriteOut,
    tags=["favorites"],
    summary="Add favorite"
)
def add_favorite(user_id: int, content_id: int):
    """Add a content to user's favorites."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO favorite (user_id, content_id) VALUES (?, ?)",
        (user_id, content_id)
    )
    fav_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"id": fav_id, "user_id": user_id, "content_id": content_id}


# PUBLIC_INTERFACE
@app.get(
    "/favorites/{user_id}",
    response_model=List[ContentOut],
    tags=["favorites"],
    summary="List user's favorites"
)
def list_favorites(user_id: int):
    """Get all favorite content for a user."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """
        SELECT content.*
        FROM content
        JOIN favorite ON content.id = favorite.content_id
        WHERE favorite.user_id=?
        """,
        (user_id,)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# PUBLIC_INTERFACE
@app.get(
    "/daily_suggestion/{user_id}",
    response_model=DailySuggestionOut,
    tags=["favorites"],
    summary="Get daily suggestion"
)
def daily_suggestion(user_id: int):
    """Suggest a random non-favorited content for user."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """
        SELECT * FROM content
        WHERE id NOT IN (
            SELECT content_id FROM favorite WHERE user_id=?
        )
        """,
        (user_id,)
    )
    rows = c.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                "No candidates for daily suggestion."
            )
        )
    row = random.choice(rows)
    return {"suggestion": dict(row)}


# -------------- TTS (Text-to-Speech) Endpoints ------------------- #

# PUBLIC_INTERFACE
@app.get(
    "/tts/{content_id}",
    tags=["tts"],
    summary="Get TTS audio for content ID"
)
def get_tts_audio(content_id: int):
    """
    Returns a stubbed TTS endpoint for content.
    (Real implementation would return or stream TTS audio file/binary.)
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM content WHERE id=?", (content_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Content not found")
    # Stubbed for demo: would use TTS library in production
    return {"text": row["text"], "tts_audio": f"TTS_AUDIO_STUB_FOR_ID_{content_id}"}


# PUBLIC_INTERFACE
@app.post(
    "/tts/batch",
    tags=["tts"],
    summary="Get batch TTS for multiple content IDs"
)
def batch_tts(req: TTSBatchRequest):
    """
    Returns a stubbed batch TTS for multiple content.
    """
    results = []
    conn = get_db()
    c = conn.cursor()
    for cid in req.content_ids:
        c.execute("SELECT * FROM content WHERE id=?", (cid,))
        row = c.fetchone()
        if row:
            results.append(
                {
                    "text": row["text"],
                    "tts_audio": f"TTS_AUDIO_STUB_FOR_ID_{cid}"
                }
            )
    conn.close()
    return results


# PUBLIC_INTERFACE
@app.get(
    "/tts/check-db",
    response_model=TTSTestResponse,
    tags=["tts"],
    summary="DB TTS check endpoint"
)
def tts_db_check():
    """
    Fetches a random sample text from DB and returns a (stubbed) TTS response
    for validation/testing purposes.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM content ORDER BY RANDOM() LIMIT 1")
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="No content in DB for TTS check.")
    # In a real TTS system, we would stream/generate TTS audio; here we stub.
    return {
        "text": row["text"],
        "tts_audio": f"TTS_AUDIO_STUB_FOR_ID_{row['id']}"
    }


# ------------------ Quiz Endpoints ------------------- #

# PUBLIC_INTERFACE
@app.post(
    "/quiz/",
    response_model=QuizOut,
    tags=["quiz"],
    summary="Create a quiz question"
)
def create_quiz(quiz: QuizCreate):
    """Add a new quiz item for content."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO quiz (content_id, question, correct_answer, distractors, language) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            quiz.content_id,
            quiz.question,
            quiz.correct_answer,
            ",".join(quiz.distractors),
            quiz.language
        )
    )
    quiz_id = c.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": quiz_id,
        "content_id": quiz.content_id,
        "question": quiz.question,
        "correct_answer": quiz.correct_answer,
        "distractors": quiz.distractors,
        "language": quiz.language,
    }


# PUBLIC_INTERFACE
@app.get(
    "/quiz/",
    response_model=List[QuizOut],
    tags=["quiz"],
    summary="List quizzes"
)
def list_quizzes(language: Optional[str] = None):
    """List all quizzes, optionally filtered by language."""
    conn = get_db()
    c = conn.cursor()
    sql = "SELECT * FROM quiz"
    params = []
    if language:
        sql += " WHERE language=?"
        params.append(language)
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    quizzes = []
    for row in rows:
        quizzes.append(
            {
                "id": row["id"],
                "content_id": row["content_id"],
                "question": row["question"],
                "correct_answer": row["correct_answer"],
                "distractors": row["distractors"].split(",") if row["distractors"] else [],
                "language": row["language"],
            }
        )
    return quizzes


# PUBLIC_INTERFACE
@app.get(
    "/quiz/{quiz_id}",
    response_model=QuizOut,
    tags=["quiz"],
    summary="Get quiz by ID"
)
def get_quiz(quiz_id: int):
    """Get one quiz by ID."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM quiz WHERE id=?", (quiz_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {
        "id": row["id"],
        "content_id": row["content_id"],
        "question": row["question"],
        "correct_answer": row["correct_answer"],
        "distractors": row["distractors"].split(",") if row["distractors"] else [],
        "language": row["language"],
    }


# PUBLIC_INTERFACE
@app.post(
    "/quiz/results",
    response_model=QuizResultOut,
    tags=["quiz"],
    summary="Submit quiz result"
)
def submit_quiz_result(result: QuizResultCreate):
    """Track a user's quiz participation/result."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO quiz_result (user_id, quiz_id, score) VALUES (?, ?, ?)",
        (result.user_id, result.quiz_id, result.score)
    )
    qresult_id = c.lastrowid
    conn.commit()
    c.execute("SELECT * FROM quiz_result WHERE id=?", (qresult_id,))
    row = c.fetchone()
    conn.close()
    return dict(row)


# PUBLIC_INTERFACE
@app.get(
    "/quiz/results/{user_id}",
    response_model=List[QuizResultOut],
    tags=["quiz"],
    summary="List user quiz results"
)
def list_user_quiz_results(user_id: int):
    """List user's quiz participation/results history."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM quiz_result WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ----------- Voice Command Interface (structure only) -------------- #

# PUBLIC_INTERFACE
@app.post(
    "/voice/command",
    tags=["voice"],
    summary="Voice command interface (structure)"
)
def voice_command(req: VoiceCommandRequest):
    """
    (Stubbed, structure only) Receives a voice command intent or raw command.
    Real logic for command parsing/dispatch would be implemented on the frontend or in a more
    advanced backend.
    """
    # Here, return a stubbed response
    # Example: If intent is 'go_to_quiz' -> give back API endpoint for quiz
    return {
        "recognized_command": req.command,
        "context": req.context,
        "action": "Not implemented - client should handle navigation"
    }


# ----------- Offline-related endpoints (optional export) ----------- #

# PUBLIC_INTERFACE
@app.get(
    "/export/userdata/{user_id}",
    tags=["user"],
    summary="Export user data (for offline access)"
)
def export_user_data(user_id: int):
    """
    Export user data, favorites, and basic history for offline load/caching.
    """
    conn = get_db()
    c = conn.cursor()
    result = {}
    c.execute("SELECT * FROM user WHERE id=?", (user_id,))
    user = c.fetchone()
    result["user"] = dict(user) if user else None
    c.execute("""
        SELECT content.*
        FROM content
        JOIN favorite ON content.id = favorite.content_id
        WHERE favorite.user_id=?
    """, (user_id,))
    favs = c.fetchall()
    result["favorites"] = [dict(row) for row in favs]
    c.execute("SELECT * FROM quiz_result WHERE user_id=?", (user_id,))
    results = c.fetchall()
    result["quiz_results"] = [dict(row) for row in results]
    conn.close()
    return result


# Swagger/OpenAPI endpoint for WebSocket usage/documentation
@app.get(
    "/websocket-usage",
    tags=["voice"],
    summary="WebSocket/voice command usage help",
    include_in_schema=True
)
def websocket_usage():
    """Explains voice command and WebSocket usage for real-time features."""
    return {
        "websocket_url": "<not-implemented>",
        "note": (
            "Voice navigation is currently structure/stub only; real-time features "
            "would use /voice/command or a websocket route."
        )
    }
