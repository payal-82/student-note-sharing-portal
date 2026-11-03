"""
Student Notes Sharing Portal
============================
A beginner-friendly Flask web application for uploading, discovering,
and downloading academic notes. Built with pure SQLite3 and vanilla CSS.
"""

import os
import sqlite3
import uuid
from functools import wraps
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
    abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# -----------------------------------------------------------------------------
# APPLICATION CONFIGURATION
# -----------------------------------------------------------------------------

# Initialize the Flask application
app = Flask(__name__)

# Secret key used for signing session cookies securely
# In production, this should be set from an environment variable
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production-12345")

# Path definitions
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "notes_portal.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# Configure upload settings
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Limit upload file size to 10 MB (10 * 1024 * 1024 bytes)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# Set of allowed file extensions for notes
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "png", "jpg", "jpeg"}

# Predefined subjects for MCA curriculum (12 Subjects)
SUBJECTS = [
    "DAA (Design & Analysis of Algorithms)",
    "TOC (Theory of Computation)",
    "Advanced Java (Lab)",
    "DBMS (Database Management Systems)",
    "Operating Systems",
    "Computer Networks",
    "Software Engineering",
    "Python Programming (Lab)",
    "Web Technologies (Lab)",
    "Machine Learning",
    "Cloud Computing",
    "Data Structures"
]

SEMESTERS = ["Sem 1", "Sem 2", "Sem 3", "Sem 4"]
NOTE_TYPES = ["Notes", "Lab Manual", "PYQ", "Assignment"]

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------------------------------------------------------------
# DATABASE HELPERS
# -----------------------------------------------------------------------------

def get_db():
    """
    Connect to the SQLite database.
    sqlite3.Row allows accessing columns by name like dictionary keys.
    """
    db = sqlite3.connect(DATABASE_PATH)
    # Enable column access by name (row['username'])
    db.row_factory = sqlite3.Row
    # Enable foreign key constraints in SQLite
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    """
    Create the database tables if they do not exist yet.
    Called automatically when the application starts.
    """
    db = get_db()
    cursor = db.cursor()

    # 1. Users table: stores user credentials and timestamps
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Notes table: stores metadata for shared documents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            semester TEXT DEFAULT 'Sem 1',
            note_type TEXT DEFAULT 'Notes',
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

    # Check and add columns if upgrading existing table
    cursor.execute("PRAGMA table_info(notes)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    if "semester" not in existing_cols:
        cursor.execute("ALTER TABLE notes ADD COLUMN semester TEXT DEFAULT 'Sem 1'")
    if "note_type" not in existing_cols:
        cursor.execute("ALTER TABLE notes ADD COLUMN note_type TEXT DEFAULT 'Notes'")

    # Ensure demo user 'payal' is initialized (hashed password for 'payal 345')
    payal_hash = "scrypt:32768:8:1$U9BEEIchRXAml9m9$f778e85c28471f4537d64f8cd30d47e67127e89a0f16680ca3a1c112f741a9f110bd742b61235365b157d2aa20581b236545f0e24c3f725d2def5c3bfaaf18d9"
    cursor.execute("SELECT id FROM users WHERE username = 'payal'")
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            ("payal", "payal@mca.edu", payal_hash)
        )
    else:
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'payal'", (payal_hash,))

    db.commit()
    db.close()


# Run table creation automatically on startup
init_db()


# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS & FILTERS
# -----------------------------------------------------------------------------

def allowed_file(filename):
    """
    Check if a file has an approved extension.
    Example: 'lecture_notes.pdf' -> True
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def format_file_size(size_in_bytes):
    """
    Converts raw byte sizes into human-readable strings (KB or MB).
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"


# Register format_file_size as a Jinja template filter
app.jinja_env.filters["filesize"] = format_file_size


@app.context_processor
def inject_global_data():
    """
    Makes current user information and subjects available to all Jinja templates.
    """
    current_user = None
    if "user_id" in session:
        current_user = {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "email": session.get("email")
        }
    return {
        "current_user": current_user,
        "all_subjects": SUBJECTS,
        "all_semesters": SEMESTERS,
        "all_types": NOTE_TYPES
    }


def login_required(f):
    """
    Decorator for views that require authentication.
    Redirects unauthenticated visitors to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# ERROR HANDLERS
# -----------------------------------------------------------------------------

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle files that exceed MAX_CONTENT_LENGTH (10 MB)."""
    flash("The selected file is too large! Maximum allowed size is 10 MB.", "error")
    return redirect(url_for("upload_note"))


@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 page not found errors."""
    return render_template("base.html", not_found=True), 404


# -----------------------------------------------------------------------------
# AUTHENTICATION ROUTES
# -----------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    User registration route.
    Hashes the user password using Werkzeug's secure hashing.
    """
    # If user is already logged in, redirect to home
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Form validation
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html", username=username, email=email)

        if len(username) < 3:
            flash("Username must be at least 3 characters long.", "error")
            return render_template("register.html", username=username, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html", username=username, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html", username=username, email=email)

        db = get_db()
        cursor = db.cursor()

        # Check for existing username or email
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            db.close()
            flash("Username or email already exists. Please pick another or log in.", "error")
            return render_template("register.html", username=username, email=email)

        # Hash password securely
        password_hash = generate_password_hash(password)

        # Insert new user record
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        db.commit()
        db.close()

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    User login route.
    Verifies password hash and initializes user session.
    """
    # If user is already logged in, redirect to home
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        login_input = request.form.get("login_input", "").strip()
        password = request.form.get("password", "")

        if not login_input or not password:
            flash("Please provide both username/email and password.", "error")
            return render_template("login.html", login_input=login_input)

        db = get_db()
        cursor = db.cursor()

        # Check by either username or email
        cursor.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (login_input, login_input.lower())
        )
        user = cursor.fetchone()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            # Save user identity in Flask session
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]

            flash(f"Welcome back, {user['username']}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page if next_page else url_for("index"))
        else:
            flash("Invalid credentials. Please check your username and password.", "error")
            return render_template("login.html", login_input=login_input)

    return render_template("login.html")


@app.route("/logout")
def logout():
    """
    Logs out the current user by clearing session data.
    """
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


# -----------------------------------------------------------------------------
# MAIN / EXPLORE ROUTE (HOME PAGE)
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Home page listing all uploaded notes in a responsive card grid.
    Includes live search (title or description) and subject filter.
    """
    search_query = request.args.get("q", "").strip()
    selected_subject = request.args.get("subject", "").strip()
    selected_semester = request.args.get("semester", "").strip()
    selected_type = request.args.get("type", "").strip()

    db = get_db()
    cursor = db.cursor()

    # Build query dynamically based on search, subject, semester, and type filters
    sql = """
        SELECT
            notes.id,
            notes.title,
            notes.subject,
            notes.semester,
            notes.note_type,
            notes.description,
            notes.original_filename,
            notes.stored_filename,
            notes.file_size,
            notes.download_count,
            notes.created_at,
            users.username AS uploader_username
        FROM notes
        JOIN users ON notes.uploader_id = users.id
        WHERE 1=1
    """
    params = []

    if search_query:
        sql += " AND (notes.title LIKE ? OR notes.description LIKE ?)"
        wildcard_query = f"%{search_query}%"
        params.extend([wildcard_query, wildcard_query])

    if selected_subject and selected_subject in SUBJECTS:
        sql += " AND notes.subject = ?"
        params.append(selected_subject)

    if selected_semester and selected_semester in SEMESTERS:
        sql += " AND notes.semester = ?"
        params.append(selected_semester)

    if selected_type and selected_type in NOTE_TYPES:
        sql += " AND notes.note_type = ?"
        params.append(selected_type)

    # Order newest first
    sql += " ORDER BY notes.created_at DESC"

    cursor.execute(sql, params)
    notes = cursor.fetchall()

    # Also count total notes in the platform for summary stats
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(download_count), 0) FROM notes")
    stats = cursor.fetchone()
    total_notes_count = stats[0] if stats else 0
    total_downloads_count = stats[1] if stats else 0

    db.close()

    return render_template(
        "index.html",
        notes=notes,
        search_query=search_query,
        selected_subject=selected_subject,
        selected_semester=selected_semester,
        selected_type=selected_type,
        total_notes_count=total_notes_count,
        total_downloads_count=total_downloads_count
    )


# -----------------------------------------------------------------------------
# UPLOAD NOTE ROUTE
# -----------------------------------------------------------------------------

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload_note():
    """
    Handles uploading a new study note.
    Requires user to be logged in.
    Validates file extension, size, and sanitizes filenames.
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        semester = request.form.get("semester", "Sem 1").strip()
        note_type = request.form.get("note_type", "Notes").strip()
        description = request.form.get("description", "").strip()
        file = request.files.get("file")

        # Validate text fields
        if not title:
            flash("Please enter a descriptive title for your note.", "error")
            return render_template("upload.html", title=title, subject=subject, semester=semester, note_type=note_type, description=description)

        if not subject or subject not in SUBJECTS:
            flash("Please select a valid academic subject from the dropdown.", "error")
            return render_template("upload.html", title=title, subject=subject, semester=semester, note_type=note_type, description=description)

        if semester not in SEMESTERS:
            semester = "Sem 1"

        if note_type not in NOTE_TYPES:
            note_type = "Notes"

        if not description:
            flash("Please enter a short description to help other students.", "error")
            return render_template("upload.html", title=title, subject=subject, semester=semester, note_type=note_type, description=description)

        # Validate file presence
        if not file or file.filename == "":
            flash("Please select a document or image file to upload.", "error")
            return render_template("upload.html", title=title, subject=subject, description=description)

        # Check allowed file extension
        if not allowed_file(file.filename):
            allowed_list = ", ".join(ALLOWED_EXTENSIONS)
            flash(f"Invalid file type. Allowed formats: {allowed_list}", "error")
            return render_template("upload.html", title=title, subject=subject, description=description)

        # Sanitize filename and generate a collision-free UUID stored name
        original_safe_name = secure_filename(file.filename)
        # In case secure_filename strips everything (e.g. non-ascii names)
        if not original_safe_name:
            original_safe_name = f"note_file.{file.filename.rsplit('.', 1)[-1].lower()}"

        unique_id = uuid.uuid4().hex
        stored_filename = f"{unique_id}_{original_safe_name}"
        destination_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_filename)

        # Save file to disk
        file.save(destination_path)
        file_size = os.path.getsize(destination_path)

        # Save metadata to SQLite
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO notes (
                title, subject, semester, note_type, description, original_filename,
                stored_filename, file_size, uploader_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '2026-11-03 10:00:00')
        """, (
            title,
            subject,
            semester,
            note_type,
            description,
            original_safe_name,
            stored_filename,
            file_size,
            session["user_id"]
        ))
        db.commit()
        db.close()

        flash("Your study note has been uploaded and published successfully!", "success")
        return redirect(url_for("my_notes"))

    return render_template("upload.html")


# -----------------------------------------------------------------------------
# DOWNLOAD ROUTE
# -----------------------------------------------------------------------------

@app.route("/download/<int:note_id>")
def download_note(note_id):
    """
    Allows anyone (logged in or guest) to download a note.
    Increments download_count in SQLite and sends the file with its original name.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()

    if not note:
        db.close()
        flash("The requested note could not be found.", "error")
        return redirect(url_for("index"))

    # Increment download counter
    cursor.execute("UPDATE notes SET download_count = download_count + 1 WHERE id = ?", (note_id,))
    db.commit()
    db.close()

    # Serve the file from the uploads directory with its original human-friendly name
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        note["stored_filename"],
        as_attachment=True,
        download_name=note["original_filename"]
    )


# -----------------------------------------------------------------------------
# MY NOTES & DELETE ROUTE (OWNER ONLY)
# -----------------------------------------------------------------------------

@app.route("/my-notes")
@login_required
def my_notes():
    """
    Displays a table of all notes uploaded by the currently logged-in user.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            subject,
            semester,
            note_type,
            description,
            original_filename,
            stored_filename,
            file_size,
            download_count,
            created_at
        FROM notes
        WHERE uploader_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],))

    user_notes = cursor.fetchall()
    db.close()

    return render_template("my_notes.html", notes=user_notes)


@app.route("/delete/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    """
    Deletes a note owned by the current user.
    POST only for security.
    Verifies ownership, removes the physical file from disk, and deletes the DB record.
    """
    db = get_db()
    cursor = db.cursor()

    # Verify that the note exists
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()

    if not note:
        db.close()
        flash("Note not found.", "error")
        return redirect(url_for("my_notes"))

    # Verify ownership: Only the uploader can delete their note
    if note["uploader_id"] != session["user_id"]:
        db.close()
        flash("Access denied: You can only delete notes that you uploaded.", "error")
        return redirect(url_for("my_notes"))

    # 1. Delete physical file from uploads/
    stored_path = os.path.join(app.config["UPLOAD_FOLDER"], note["stored_filename"])
    if os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except OSError as e:
            # Continue deleting database record even if file removal triggers an error
            print(f"Warning: Failed to delete file {stored_path}: {e}")

    # 2. Delete database entry
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    db.close()

    flash(f"Note '{note['title']}' was deleted successfully.", "success")
    return redirect(url_for("my_notes"))


# -----------------------------------------------------------------------------
# RUN APPLICATION
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Host on 127.0.0.1 (localhost) on port 5000 with debug enabled for development
    app.run(host="127.0.0.1", port=5000, debug=True)
