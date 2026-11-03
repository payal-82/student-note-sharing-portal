"""
Migration script to initialize Neon PostgreSQL database and seed MCA data.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DEFAULT_DEMO_USER

NEON_DATABASE_URL = "postgresql://neondb_owner:npg_tDgwchG0AzP7@ep-morning-shadow-bee13hno-pooler.c-9.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

MCA_SAMPLE_NOTES = [
    {
        "title": "Divide & Conquer, Greedy and Dynamic Programming Notes",
        "subject": "DAA (Design & Analysis of Algorithms)",
        "semester": "Sem 2",
        "note_type": "Notes",
        "description": "Comprehensive algorithmic guide covering Merge Sort, Quick Sort, Fractional & 0/1 Knapsack, Huffman Coding, Dijkstra shortest path, and Bellman-Ford complexity analysis.",
        "filename": "DAA_Divide_Conquer_Greedy_DP_Notes.pdf",
        "content": b"%PDF-1.4 MCA Sem 2: DAA - Divide & Conquer, Greedy Method, Dynamic Programming, Asymptotic Notations.",
        "downloads": 48
    },
    {
        "title": "DFA, NFA, Regular Expressions & Turing Machines",
        "subject": "TOC (Theory of Computation)",
        "semester": "Sem 2",
        "note_type": "Notes",
        "description": "In-depth theoretical computer science notes: Deterministic/Nondeterministic finite automata, state minimization, Pumping Lemma for regular languages, CFG, PDA, and Turing Machine decidability.",
        "filename": "TOC_Automata_Turing_Machines_Complete.pdf",
        "content": b"%PDF-1.4 MCA Sem 2: TOC - DFA, NFA, Regular Expressions, Pumping Lemma, Pushdown Automata, Turing Machines.",
        "downloads": 35
    },
    {
        "title": "JDBC, Servlets & JSP Lab Programs with Output",
        "subject": "Advanced Java (Lab)",
        "semester": "Sem 3",
        "note_type": "Lab Manual",
        "description": "Practical manual containing complete tested Java code: Database connectivity (JDBC), HTTP Servlet request dispatching, JSP session handling, MVC architecture, and Spring Boot / Hibernate basics.",
        "filename": "Adv_Java_Lab_Manual_JDBC_JSP_Spring.pdf",
        "content": b"%PDF-1.4 MCA Sem 3: Advanced Java Lab Manual - JDBC, Servlets, JSP, Hibernate ORM, Spring Boot REST API.",
        "downloads": 62
    },
    {
        "title": "Normalization, SQL Queries & Transactions",
        "subject": "DBMS (Database Management Systems)",
        "semester": "Sem 1",
        "note_type": "Notes",
        "description": "Essential relational database concepts: 1NF through BCNF normalization with solved anomalies, complex nested SQL queries & joins, ACID properties, and concurrency control protocols.",
        "filename": "DBMS_Normalization_SQL_Transactions.pdf",
        "content": b"%PDF-1.4 MCA Sem 1: DBMS - Functional Dependencies, Normalization (1NF-BCNF), SQL Joins, Concurrency Control.",
        "downloads": 54
    },
    {
        "title": "Process Scheduling, Deadlocks & Memory Management",
        "subject": "Operating Systems",
        "semester": "Sem 2",
        "note_type": "Notes",
        "description": "Core operating system lecture notes covering CPU scheduling algorithms (FCFS, SJF, Round Robin), Banker's algorithm for deadlock avoidance, virtual memory paging, and TLB replacement policies.",
        "filename": "OS_Scheduling_Deadlocks_VirtualMemory.pdf",
        "content": b"%PDF-1.4 MCA Sem 2: Operating Systems - Process Scheduling, Semaphores, Deadlocks, Paging, Page Replacement.",
        "downloads": 41
    },
    {
        "title": "SDLC Models, UML Diagrams & Testing",
        "subject": "Software Engineering",
        "semester": "Sem 1",
        "note_type": "Notes",
        "description": "Software engineering fundamentals: Waterfall vs Agile Scrum models, SRS documentation, UML class/use-case/sequence diagrams, black-box vs white-box test cases, and CI/CD pipelines.",
        "filename": "Software_Engineering_SDLC_UML_Testing.pdf",
        "content": b"%PDF-1.4 MCA Sem 1: Software Engineering - SDLC Models, Agile, UML Diagrams, Black-Box/White-Box Testing.",
        "downloads": 29
    },
    {
        "title": "Machine Learning End-Term PYQ Papers (2022-2025) with Solutions",
        "subject": "Machine Learning",
        "semester": "Sem 3",
        "note_type": "PYQ",
        "description": "Solved university previous year exam papers covering Supervised Learning (Linear Regression, SVM), Unsupervised Clustering (K-Means), Decision Trees, and Neural Network backpropagation.",
        "filename": "ML_University_PYQ_Papers_Solved_2022_2025.pdf",
        "content": b"%PDF-1.4 MCA Sem 3: Machine Learning Previous Year Question Papers with Step-by-Step Solutions.",
        "downloads": 73
    },
    {
        "title": "Python Programming & Data Science Lab Experiments",
        "subject": "Python Programming (Lab)",
        "semester": "Sem 1",
        "note_type": "Lab Manual",
        "description": "Lab record covering Python OOP, NumPy multidimensional arrays, Pandas data wrangling, Matplotlib visualization, and CSV/JSON file handling with sample inputs and execution outputs.",
        "filename": "Python_Lab_Manual_DataScience_OOP.pdf",
        "content": b"%PDF-1.4 MCA Sem 1: Python Programming Lab Manual - OOP, NumPy, Pandas, Matplotlib, Data Analysis.",
        "downloads": 38
    }
]

def migrate():
    print("Connecting to Neon PostgreSQL database...")
    conn = psycopg2.connect(NEON_DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Users table verified.")

    # 2. Create notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            subject VARCHAR(150) NOT NULL,
            semester VARCHAR(50) DEFAULT 'Sem 1',
            note_type VARCHAR(50) DEFAULT 'Notes',
            description TEXT NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            stored_filename VARCHAR(255) NOT NULL,
            file_size BIGINT NOT NULL,
            uploader_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            download_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Notes table verified.")

    # 3. Upsert user 'payal'
    cursor.execute("SELECT id FROM users WHERE username = %s;", (DEFAULT_DEMO_USER["username"],))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s) RETURNING id;
        """, (DEFAULT_DEMO_USER["username"], DEFAULT_DEMO_USER["email"], DEFAULT_DEMO_USER["password_hash"]))
        payal_id = cursor.fetchone()["id"]
        print(f"User 'payal' created with id {payal_id}.")
    else:
        payal_id = row["id"]
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s;", (DEFAULT_DEMO_USER["password_hash"], payal_id))
        print(f"User 'payal' exists (id {payal_id}), password hash refreshed.")

    # 4. Sync sample notes (ensure physical files also exist in uploads/)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(base_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    cursor.execute("DELETE FROM notes;")
    print("Refreshing sample notes in Neon database...")

    import uuid
    for note in MCA_SAMPLE_NOTES:
        stored_name = f"{uuid.uuid4().hex}_{note['filename']}"
        file_path = os.path.join(upload_dir, stored_name)
        with open(file_path, "wb") as f:
            f.write(note["content"])
        file_size = len(note["content"])

        cursor.execute("""
            INSERT INTO notes (
                title, subject, semester, note_type, description,
                original_filename, stored_filename, file_size,
                uploader_id, download_count, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '2026-11-03 10:00:00');
        """, (
            note["title"],
            note["subject"],
            note["semester"],
            note["note_type"],
            note["description"],
            note["filename"],
            stored_name,
            file_size,
            payal_id,
            note["downloads"]
        ))

    cursor.execute("SELECT COUNT(*) AS cnt FROM notes;")
    cnt = cursor.fetchone()["cnt"]
    print(f"Neon database successfully populated with {cnt} notes for user payal!")
    conn.close()

if __name__ == "__main__":
    migrate()

