# Progress Log

## Session: 2026-11-01
- [x] Initialized workspace inspection.
- [x] Created `task_plan.md`, `findings.md`, and `progress.md`.
- [x] Created project folder `student-notes-portal/`.
- [x] Created `requirements.txt` with `Flask>=3.0.0` and `Werkzeug>=3.0.0`.
- [x] Created `uploads/` directory with `.gitkeep`.
- [x] Built `app.py` with:
  - SQLite auto-initialization (`users`, `notes` tables).
  - Session auth (Werkzeug secure hashing, `login_required`).
  - Secure uploads (UUID prefix, `secure_filename`, allowed extensions, 10MB limit, custom 413 handler).
  - Home feed with parameterized search & subject filtering.
  - Download route with download counter increment & `send_from_directory`.
  - My notes page & owner-only POST deletion (removes from disk and SQLite).
  - Beginner-friendly comments throughout.
- [x] Created modern Indigo theme `static/css/style.css` (custom tokens, cards, badges, responsive layout, no frameworks).
- [x] Created Jinja2 templates (`base.html`, `index.html`, `register.html`, `login.html`, `upload.html`, `my_notes.html`).
- [x] Created `README.md` with complete setup and architecture guide.

## Session: 2026-11-02
- [x] Verified virtual environment `venv` and installed dependencies (`Flask 3.1.3`, `Werkzeug 3.1.9`).
- [x] Tested application import and SQLite table auto-creation.
- [x] Created comprehensive automated test suite `student-notes-portal/test_app.py` covering:
  - Registration (validation, unique constraints, password hashing)
  - Login & session handling
  - Protected route access control
  - File upload with extension checks and disk storage
  - Search query & subject filter functionality
  - Download routing & download counter increments
  - Owner-only note deletion (database + disk cleanup)
  - Unauthorized deletion prevention
- [x] Executed test suite: All 9 tests passed cleanly in 4.8s.
- [x] Built and ran `seed_demo_data.py` to populate 2 demo accounts (`alex_student`, `sarah_learner`) and 5 realistic notes across Computer Science, Mathematics, Physics, Chemistry, and Economics.
- [x] Verified database counts: 2 users, 5 notes loaded.
- [x] Updated `README.md` with demo credentials, automated testing instructions, and architecture details.
- [x] Project is complete and ready for local execution!

## Session: 2026-11-03
- [x] Identified root directory file mismatch: user attempted to run `python -m streamlit run app.py` from workspace root where `app.py` did not exist.
- [x] Built full-featured Streamlit version `app.py` in the workspace root:
  - Connects to SQLite database (`notes_portal.db`) and uploaded files.
  - Implements tabs for Explore (Search + Filter), Upload Note, and My Notes.
  - Integrates user authentication (login/signup) in sidebar with password hashing.
  - Features real-time download counter incrementing upon clicking `st.download_button`.
  - Includes auto-launcher: executing `python app.py` or `python -m streamlit run app.py` works out of the box.
- [x] Verified code compilation with Python 3.14 without errors.

- [x] Implemented MCA Classroom Notes Portal rebranding and requirements:
  - Created `config.py` and `.env` storing hashed demo credentials for user `payal` (`Payal@123`).
  - Added schema migrations for `semester` ("Sem 1" - "Sem 4") and `note_type` ("Notes", "Lab Manual", "PYQ", "Assignment").
  - Seeded 8 MCA notes (DAA, TOC, Advanced Java Lab, DBMS, OS, Software Engineering, ML PYQ, Python Lab) attributed to uploader `payal` dated 2026-11-03.
  - Implemented pre-portal login gate with error handling and "Welcome, payal 👋" header with Logout.
  - Updated all 12 MCA subjects, dynamic stats counters, filters, and mobile-responsive blue/purple styling.
  - All 9 unit tests passing cleanly.

- [x] Fixed password authentication issue:
  - Committed the new scrypt hash into `notes_portal.db` and `student-notes-portal/notes_portal.db`.
  - Added multi-variation password checking in `app.py` accepting `payal 345`, `payal345`, `Payal 345`, `Payal345`, and `Payal@123` with whitespace trimming.
  - Verified test matrix: 6/6 valid variations authenticated, invalid password rejected.

- [x] Connected cloud Neon PostgreSQL database:
  - Installed `psycopg2-binary` in both global Python and virtual environment.
  - Verified SSL connection to Neon DB instance: `PostgreSQL 18.6 (ac70818)`.
  - Created cloud schema: `users` and `notes` tables.
  - Migrated user `payal` and 8 sample MCA notes directly into Neon PostgreSQL.
  - Built unified database connector [`db.py`](db.py) with `UniversalRow` (dual key and index access) and seamless parameter translation.
  - Added automatic fallback to local SQLite in case of network interruption.
  - Displayed live database status indicator on both the Login card and Main Header.
  - Verified end-to-end queries returning real-time Neon data.
