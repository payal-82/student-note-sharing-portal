"""
Seed script to populate Student Notes Portal with demo users and realistic study notes.
"""

import os
import sqlite3
import uuid
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "notes_portal.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def seed():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Ensure tables exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            uploader_id INTEGER NOT NULL,
            download_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploader_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Create demo users
    demo_users = [
        ("alex_student", "alex@university.edu", "student123"),
        ("sarah_learner", "sarah@university.edu", "student123")
    ]

    user_ids = {}
    for username, email, raw_pwd in demo_users:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            hashed = generate_password_hash(raw_pwd)
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hashed))
            user_ids[username] = cursor.lastrowid
        else:
            user_ids[username] = row["id"]

    sample_notes = [
        {
            "title": "Data Structures & Algorithms Cheat Sheet",
            "subject": "Computer Science",
            "description": "Comprehensive reference guide covering Big-O complexities, Hash Maps, Binary Search Trees, Graphs, Dijkstra, and Dynamic Programming templates.",
            "filename": "dsa_quick_reference.pdf",
            "content": b"%PDF-1.4 Data Structures and Algorithms Comprehensive Review Notes: Arrays, Linked Lists, Trees, Graphs, Sorting algorithms, Dynamic Programming.",
            "uploader": "alex_student",
            "downloads": 14
        },
        {
            "title": "Calculus II - Integration Techniques & Series",
            "subject": "Mathematics",
            "description": "Clear step-by-step notes on integration by parts, trigonometric substitution, Taylor & Maclaurin series, and convergence tests.",
            "filename": "calculus_integration_notes.pdf",
            "content": b"%PDF-1.4 Calculus II: Techniques of Integration, Improper Integrals, Infinite Sequences and Series.",
            "uploader": "alex_student",
            "downloads": 28
        },
        {
            "title": "Quantum Physics - Wave Mechanics & Operators",
            "subject": "Physics",
            "description": "Lecture notes covering the Schrodinger wave equation, infinite potential wells, quantum tunneling, and angular momentum operators.",
            "filename": "quantum_mechanics_lecture.pdf",
            "content": b"%PDF-1.4 Quantum Physics: Wavefunctions, Postulates of Quantum Mechanics, Harmonic Oscillator.",
            "uploader": "sarah_learner",
            "downloads": 9
        },
        {
            "title": "Organic Chemistry - Reaction Mechanisms",
            "subject": "Chemistry",
            "description": "Handy visual summary of SN1, SN2, E1, E2 mechanisms, electrophilic aromatic substitution, and resonance stability rules.",
            "filename": "organic_chem_mechanisms.pdf",
            "content": b"%PDF-1.4 Organic Chemistry: Nucleophilic Substitution, Elimination Reactions, Stereochemistry.",
            "uploader": "sarah_learner",
            "downloads": 42
        },
        {
            "title": "Macroeconomics Principles & Monetary Policy",
            "subject": "Economics",
            "description": "Exam revision notes explaining GDP components, inflation dynamics, IS-LM model, central banking, and open economy interest rates.",
            "filename": "macroeconomics_revision.pdf",
            "content": b"%PDF-1.4 Macroeconomics: Aggregate Supply and Demand, Fiscal Policy, Monetary Multipliers.",
            "uploader": "alex_student",
            "downloads": 19
        }
    ]

    for item in sample_notes:
        # Check if already exists
        cursor.execute("SELECT id FROM notes WHERE title = ?", (item["title"],))
        if cursor.fetchone():
            continue

        stored_name = f"{uuid.uuid4().hex}_{item['filename']}"
        file_path = os.path.join(UPLOAD_FOLDER, stored_name)
        with open(file_path, "wb") as f:
            f.write(item["content"])
        file_size = len(item["content"])

        cursor.execute("""
            INSERT INTO notes (
                title, subject, description, original_filename,
                stored_filename, file_size, uploader_id, download_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["title"],
            item["subject"],
            item["description"],
            item["filename"],
            stored_name,
            file_size,
            user_ids[item["uploader"]],
            item["downloads"]
        ))

    conn.commit()
    conn.close()
    print("Seeding complete! 2 demo users and 5 sample notes loaded.")

if __name__ == "__main__":
    seed()

