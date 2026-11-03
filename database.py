import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).with_name("quizlab.db")
conn = sqlite3.connect(str(DB_FILE))
cur = conn.cursor()
conn.execute("PRAGMA foreign_keys = ON;")

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('Admin', 'Student')) NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
)
""")

# SUBJECTS
cur.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))
)
""")

# QUIZZES
cur.execute("""
CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    instructions TEXT,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
    total_marks REAL NOT NULL DEFAULT 0 CHECK(total_marks >= 0),
    passing_marks REAL NOT NULL DEFAULT 0 CHECK(passing_marks >= 0),
    start_time TEXT,
    end_time TEXT,
    status TEXT DEFAULT 'Draft' CHECK(status IN ('Draft', 'Published', 'Closed')),
    created_by INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    CHECK(passing_marks <= total_marks OR total_marks = 0),
    CHECK(end_time IS NULL OR start_time IS NULL OR end_time >= start_time)
)
""")

# QUESTIONS
cur.execute("""
CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL DEFAULT 'MCQ' CHECK(question_type IN ('MCQ', 'MSQ')),
    difficulty TEXT DEFAULT 'Medium' CHECK(difficulty IN ('Easy', 'Medium', 'Hard')),
    explanation TEXT,
    created_by INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE RESTRICT
)
""")

# OPTIONS
cur.execute("""
CREATE TABLE IF NOT EXISTS options (
    option_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    is_correct INTEGER DEFAULT 0 CHECK(is_correct IN (0, 1)),
    option_order INTEGER NOT NULL DEFAULT 1 CHECK(option_order > 0),
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE,
    UNIQUE(question_id, option_order)
)
""")

# QUIZ QUESTIONS
cur.execute("""
CREATE TABLE IF NOT EXISTS quiz_questions (
    quiz_question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    marks REAL NOT NULL DEFAULT 1 CHECK(marks >= 0),
    question_order INTEGER NOT NULL DEFAULT 1 CHECK(question_order > 0),
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE RESTRICT,
    UNIQUE(quiz_id, question_id),
    UNIQUE(quiz_id, question_order)
)
""")

# QUIZ ATTEMPTS
cur.execute("""
CREATE TABLE IF NOT EXISTS quiz_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    submitted_at TEXT,
    score REAL NOT NULL DEFAULT 0 CHECK(score >= 0),
    total_marks REAL NOT NULL DEFAULT 0 CHECK(total_marks >= 0),
    percentage REAL NOT NULL DEFAULT 0 CHECK(percentage >= 0 AND percentage <= 100),
    status TEXT DEFAULT 'In Progress' CHECK(status IN ('In Progress', 'Submitted', 'Timed Out')),
    result_status TEXT CHECK(result_status IN ('Pass', 'Fail') OR result_status IS NULL),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE RESTRICT
)
""")

# ATTEMPT ANSWERS
cur.execute("""
CREATE TABLE IF NOT EXISTS attempt_answers (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    quiz_question_id INTEGER NOT NULL,
    selected_option_ids TEXT NOT NULL DEFAULT '[]',
    is_correct INTEGER CHECK(is_correct IN (0, 1) OR is_correct IS NULL),
    marks_obtained REAL NOT NULL DEFAULT 0 CHECK(marks_obtained >= 0),
    answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(attempt_id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_question_id) REFERENCES quiz_questions(quiz_question_id) ON DELETE RESTRICT,
    UNIQUE(attempt_id, quiz_question_id)
)
""")

cur.execute("""
INSERT OR IGNORE INTO users(name, email, password, role) VALUES (?, ?, ?, ?) """,
            ('QuizLab Admin', 'admin@gmail.com', 'admin@123', 'Admin'))

cur.execute("""
INSERT OR IGNORE INTO users(name, email, password, role) VALUES (?, ?, ?, ?) """,
            ('Student', 'student@gmail.com', 'student@123', 'Student'))

cur.execute("""
INSERT OR IGNORE INTO subjects (subject_name, description) VALUES (?, ?) """,
            ("Python Basics", "Fundamentals of Python programming"))

cur.execute("SELECT * FROM users")
print(cur.fetchall())

cur.execute("SELECT * FROM subjects")
print(cur.fetchall())

cur.execute("SELECT * FROM quizzes")
print(cur.fetchall())

cur.execute("SELECT * FROM questions")
print(cur.fetchall())

cur.execute("SELECT * FROM options")
print(cur.fetchall())

cur.execute("SELECT * FROM quiz_questions")
print(cur.fetchall())

cur.execute("SELECT * FROM quiz_attempts")
print(cur.fetchall())

cur.execute("SELECT * FROM attempt_answers")
print(cur.fetchall())

conn.commit()
conn.close()
