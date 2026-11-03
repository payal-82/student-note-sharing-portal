# Findings & Research Notes

## Environment & Prerequisites
- OS: Windows
- Python Version: Python 3.14.4
- Working directory: `c:\Users\HP\OneDrive\Desktop\student note sharing portal`
- Target folder: `student-notes-portal`

## Architecture Decisions & Constraints
- Database: Pure SQLite via standard library `sqlite3`. Using `sqlite3.Row` for dict-like attribute access.
- Auto-initialization: `init_db()` runs on application startup or first request if the database file does not exist.
- File Uploads:
  - Allowed extensions: `{'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'png', 'jpg', 'jpeg'}`
  - Naming strategy: `<uuid4>_<secure_filename(original_name)>` to guarantee no namespace collision and safety against directory traversal.
  - Storage location: `uploads/` within `student-notes-portal`.
  - Max file size: 10 MB configured in Flask (`MAX_CONTENT_LENGTH = 10 * 1024 * 1024`), with custom 413 error handler returning a friendly flash message.
- Design System:
  - Palette: Indigo primary (`#4f46e5`, `#4338ca`, `#3730a3`), slate neutrals (`#f8fafc`, `#f1f5f9`, `#e2e8f0`, `#64748b`, `#0f172a`), emerald accents for downloads/success, amber for warnings, rose for errors/delete.
  - Clean card grid layout with hover elevation and responsive flex/grid columns.
  - Accessible input controls and semantic HTML elements.
