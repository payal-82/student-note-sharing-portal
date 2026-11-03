# Task Plan: Student Notes Sharing Portal

## Project Goal
Build a beginner-level "Student Notes Sharing Portal" web application in a new directory `student-notes-portal` using Flask, pure SQLite (sqlite3), vanilla HTML/CSS, with user authentication, note uploads (with type/size validation), card-grid exploration with search and subject filtering, download tracking, owner-only deletion, flash notifications, and clean beginner-friendly comments. Afterwards, set up a virtual environment, install dependencies, run the app, and comprehensively test all user flows in the browser.

## Architectural Overview
- **Backend**: Python Flask (`app.py`), using `sqlite3` with `sqlite3.Row` factory for dictionary-like database rows.
- **Security**: Password hashing using `werkzeug.security.generate_password_hash` & `check_password_hash`, session-based authentication with `login_required` decorator.
- **File Uploads**: `uploads/` folder, UUID prefix + `secure_filename`, extension check (`pdf, doc, docx, ppt, pptx, txt, png, jpg, jpeg`), max 10MB (`app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024`).
- **Database Schema**:
  - `users` table: `id`, `username` (unique), `email` (unique), `password_hash`, `created_at`
  - `notes` table: `id`, `title`, `subject`, `description`, `original_filename`, `stored_filename`, `file_size`, `uploader_id`, `download_count`, `created_at`
- **Frontend**: Responsive modern CSS with an Indigo theme (CSS variables, modern typography, card grid, badges, accessible forms, alert banners).
- **Templates**: `base.html`, `index.html`, `register.html`, `login.html`, `upload.html`, `my_notes.html`.

## Phases & Status

- [x] **Phase 1: Project Setup & Database Architecture**
  - Create directory `student-notes-portal`
  - Create `requirements.txt` (`Flask>=3.0.0`, `Werkzeug>=3.0.0`)
  - Create `uploads/` directory and `.gitkeep`
  - Write `app.py` foundational setup: DB initialization (`init_db`), connection helpers (`get_db`), table schema with indices
  - Status: completed

- [x] **Phase 2: Authentication & Core Business Logic (Backend)**
  - Auth routes: `/register`, `/login`, `/logout` with flash feedback
  - Upload route: `/upload` (subject dropdown, file validation, UUID storage, metadata recording)
  - Home & Explore route: `/` (card listing, search query parameter `q`, subject filter parameter `subject`, sorting)
  - Download route: `/download/<int:note_id>` (increment counter, `send_from_directory`)
  - Manage notes route: `/my-notes` and `/delete/<int:note_id>` (POST only, authorization check, remove file from disk and database)
  - Error handlers: 404, 413 (File too large), 500
  - Status: completed

- [x] **Phase 3: Jinja2 Templates & Modern Indigo CSS**
  - Create `static/css/style.css` (custom design system, indigo palette, card grid, badges, search bar, modals/alerts, responsive layout)
  - Create `templates/base.html` (semantic navbar, flash messages container, main container, footer)
  - Create `templates/index.html` (hero banner, search box, subject filter pills/dropdown, notes cards grid with stats)
  - Create `templates/register.html` & `templates/login.html` (centered auth card, form validation styling)
  - Create `templates/upload.html` (file dropzone/input, subject selector, title, description)
  - Create `templates/my_notes.html` (table of user's uploaded notes, stats, download link, delete form with confirmation)
  - Write comprehensive beginner-friendly `README.md`
  - Status: completed

- [x] **Phase 4: Virtual Environment & Dependency Installation**
  - Create virtual environment `venv` in `student-notes-portal`
  - Install dependencies from `requirements.txt`
  - Test database initialization and syntax
  - Status: completed

- [x] **Phase 5: Automated Testing & Verification**
  - Build automated test suite (`test_app.py`) covering all 9 test scenarios:
    1. User registration, password hashing & validation
    2. User login & session authentication
    3. Note uploads with extension validation & UUID storage
    4. Access control redirects for unauthenticated users
    5. Homepage discovery, query search & subject filtering
    6. Download route serving file with original filename & incrementing counter
    7. Owner-only note deletion (database + disk cleanup)
    8. Cross-user delete authorization block
  - Run full test suite: 9/9 tests passed with 0 errors
  - Status: completed

- [x] **Phase 6: Seeding Demo Data & Documentation**
  - Create `seed_demo_data.py` with 2 demo accounts and 5 academic notes across subjects
  - Seed database and upload directory
  - Update `README.md` with walkthrough, demo credentials, and test commands
  - Status: completed
