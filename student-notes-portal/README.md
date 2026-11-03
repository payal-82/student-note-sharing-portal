# 📚 Student Notes Sharing Portal

A beginner-friendly, lightweight web application built with **Python Flask**, **SQLite3** (standard library, no heavy ORM), **HTML5**, and modern **vanilla CSS** (Indigo theme, responsive card grid, zero frontend frameworks).

---

## ✨ Features

1. **User Authentication**:
   - Register new user accounts with username, email, and password.
   - Secure password hashing with `werkzeug.security` (`generate_password_hash` & `check_password_hash`).
   - Flask session-based authentication with `login_required` route decorator.
   - User logout with session cleanup.

2. **Note Uploads (Logged-in Students)**:
   - Form fields: Document Title, Academic Subject (Dropdown), Description, and File.
   - Allowed file types: `.pdf`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.txt`, `.png`, `.jpg`, `.jpeg`.
   - File size validation capped at 10 MB with friendly error handling.
   - Secure file storage with `uuid` prefix + `werkzeug.utils.secure_filename` to prevent file collisions and directory traversal attacks.

3. **Homepage Discovery & Search**:
   - Responsive card grid displaying all notes.
   - Information displayed on each card: Title, Subject badge, Description, Uploader username, Upload date, and Download counter.
   - Full-text search across titles and descriptions.
   - Subject category filter dropdown.

4. **Note Downloads & Metrics**:
   - Open to anyone (both registered students and guests).
   - Each download automatically increments the database download counter.
   - Download serves the file with its original human-readable filename.

5. **My Notes Management (Owner Only)**:
   - Dedicated table listing all notes uploaded by the logged-in user.
   - Owner-only delete functionality via `POST` requests.
   - Deletion removes the database record **and** permanently purges the stored physical file from disk.

6. **User Feedback & Aesthetics**:
   - Rich flash notification alerts for success, error, warning, and info states.
   - Modern Indigo UI with card hover elevations, badges, and responsive design for desktop and mobile.

---

## 📁 Project Structure

```text
student-notes-portal/
├── app.py                  # Core Flask app, SQLite database helpers, routes, and logic
├── requirements.txt        # Minimal dependencies (Flask, Werkzeug)
├── uploads/                # Directory storing physical uploaded documents and images
├── static/
│   └── css/
│       └── style.css       # Clean, modern Indigo design system (no frameworks)
├── templates/              # Jinja2 template inheritance
│   ├── base.html           # Master layout: navigation bar, flash alerts, footer
│   ├── index.html          # Homepage: hero stats, search/filter bar, notes card grid
│   ├── register.html       # Student sign up form
│   ├── login.html          # Student login form
│   ├── upload.html         # Study note upload form with dropzone
│   └── my_notes.html       # Personal dashboard table with delete button
└── README.md               # Beginner guide and documentation
```

---

## 🚀 Setup and Run Instructions

### 1. Prerequisites
- **Python 3.8+** installed on your system.
- Terminal or PowerShell.

### 2. Open Terminal and Navigate to the Folder
```bash
cd student-notes-portal
```

### 3. Create a Virtual Environment
- On **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- On **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```

You should see output similar to:
```text
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 6. Open in Your Browser
Open your favorite browser and visit:
```text
http://127.0.0.1:5000
```

### 7. Demo Accounts & Pre-Loaded Data
The platform includes pre-seeded study notes and demo accounts ready to test immediately:
- **User 1**: Username: `alex_student` | Password: `student123`
- **User 2**: Username: `sarah_learner` | Password: `student123`

You can also re-seed or reset demo notes anytime by running:
```bash
python seed_demo_data.py
```

### 8. Run Automated Test Suite
To run all 9 comprehensive integration and unit tests:
```bash
python test_app.py -v
```

---

## 🛠️ Step-by-Step Beginner Walkthrough

1. **Sign Up**: Click **Sign Up** in the top navigation, enter a username, email, and password.
2. **Log In**: Enter your credentials to start your session.
3. **Upload a Note**: Click **Upload Note**, provide a title, choose a subject (e.g. *Computer Science*), write a description, and select a file (`.pdf`, `.txt`, `.png`, etc.).
4. **Search and Filter**: Return to the home page. Test the search bar by typing a keyword or selecting a subject from the dropdown.
5. **Download**: Click the **Download** button on any card. Notice how the download counter increments.
6. **Manage & Delete**: Visit **My Notes** in the navigation bar to see your uploaded items. Click **Delete** to safely remove a note from both the database and the physical disk.

---

## 🔒 Security Best Practices Implemented

- **Password Hashing**: Passwords are never stored in plain text. Werkzeug generates a salted, one-way hash.
- **Path Traversal Protection**: Uploaded filenames are sanitized with `secure_filename()` and stored with a unique `UUID` prefix on disk, preventing overwriting or directory traversal attacks.
- **Strict Authorization**: Only the original uploader can delete their note (`POST` method only, verified against `session['user_id']`).
- **File Size Capping**: Flask's `MAX_CONTENT_LENGTH = 10 * 1024 * 1024` protects against denial-of-service via huge file payloads.
- **SQL Injection Prevention**: All SQLite queries use parameterized queries (`?` placeholders).
