"""
🎓 MCA Classroom Notes Portal
=============================
A modern, collaborative platform for MCA students to explore, upload,
and download class notes, lab manuals, and previous year papers.
Built with pure SQLite3 and Streamlit.
"""

import os
import sys
import uuid
import sqlite3
import datetime
import subprocess
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import streamlit as st

# Import demo credentials from configuration (demo purposes only)
from config import DEFAULT_DEMO_USER

# -----------------------------------------------------------------------------
# APPLICATION CONFIGURATION & PATHS
# -----------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database and upload directories
DATABASE_PATH = os.path.join(BASE_DIR, "notes_portal.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions for study documents
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "png", "jpg", "jpeg"}

# MCA Curriculum Subjects (12 Subjects)
MCA_SUBJECTS = [
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

# -----------------------------------------------------------------------------
# DATABASE SETUP & HELPERS (NEON POSTGRESQL + SQLITE FALLBACK)
# -----------------------------------------------------------------------------

from db import get_db, init_db, get_db_status

init_db()

def format_file_size(size_in_bytes):
    """Format bytes into readable units."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"

def increment_download(note_id):
    """Increment download count in database on click."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET download_count = download_count + 1 WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# PAGE STYLING (MODERN BLUE/PURPLE THEME & RESPONSIVE DESIGN)
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="🎓 MCA Classroom Notes Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Responsive Blue/Purple CSS Tokens
st.markdown("""
<style>
    :root {
        --primary: #4f46e5;
        --primary-hover: #4338ca;
        --secondary: #2563eb;
        --purple-bg: #f5f3ff;
        --card-border: #e0e7ff;
    }
    
    /* Top Header Branding */
    .portal-hero {
        background: linear-gradient(135deg, #3730a3 0%, #4f46e5 50%, #2563eb 100%);
        border-radius: 16px;
        padding: 1.8rem 2rem;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.25);
    }
    .portal-hero h1 {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        color: #ffffff !important;
        letter-spacing: -0.02em;
    }
    .portal-hero p {
        font-size: 1.05rem;
        margin-top: 0.5rem;
        color: #e0e7ff;
        margin-bottom: 0;
        max-width: 850px;
        line-height: 1.5;
    }
    
    /* Login Card Container */
    .login-container {
        max-width: 480px;
        margin: 3rem auto;
        padding: 2.2rem 2rem;
        background: #ffffff;
        border-radius: 18px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
        text-align: center;
    }
    
    /* Badges */
    .badge-subject {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #e0e7ff;
        color: #3730a3;
        margin-right: 0.35rem;
        margin-bottom: 0.4rem;
    }
    .badge-sem {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #f3e8ff;
        color: #6b21a8;
        margin-right: 0.35rem;
        margin-bottom: 0.4rem;
    }
    .badge-type {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #dbeafe;
        color: #1e40af;
        margin-bottom: 0.4rem;
    }
    .badge-lab {
        background-color: #d1fae5;
        color: #065f46;
    }
    .badge-pyq {
        background-color: #fef3c7;
        color: #92400e;
    }
    .badge-assignment {
        background-color: #ede9fe;
        color: #5b21b6;
    }

    /* User Greeting Pill */
    .user-greeting-pill {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.4rem 1rem;
        border-radius: 9999px;
        backdrop-filter: blur(8px);
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 600;
        color: #ffffff;
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .portal-hero {
            padding: 1.3rem 1.2rem;
        }
        .portal-hero h1 {
            font-size: 1.6rem;
        }
        .portal-hero p {
            font-size: 0.95rem;
        }
        .login-container {
            margin: 1rem auto;
            padding: 1.5rem 1.2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE & AUTHENTICATION
# -----------------------------------------------------------------------------

if "user" not in st.session_state:
    st.session_state["user"] = None

# =============================================================================
# VIEW 1: LOGIN PAGE (Shown BEFORE the portal if user is not logged in)
# =============================================================================

if not st.session_state["user"]:
    col_l, col_center, col_r = st.columns([1, 1.8, 1])
    
    with col_center:
        st.write("")
        st.write("")
        
        # Centered Branding
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 3.2rem; margin-bottom: 0.5rem;">🎓</div>
            <h1 style="color: #3730a3; font-weight: 800; font-size: 2rem; margin-bottom: 0.4rem;">MCA Classroom Notes Portal</h1>
            <p style="color: #64748b; font-size: 1rem; line-height: 1.5;">
                Collaborative platform for MCA students to explore, upload, and download class notes, lab manuals, and previous year papers.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### 🔐 Student Login")
            st.caption("Please sign in with your credentials to access class materials.")
            
            with st.form("portal_login_form"):
                username_input = st.text_input("Username or Email", placeholder="e.g. payal", value="payal")
                password_input = st.text_input("Password", type="password", placeholder="Enter your password")
                login_submitted = st.form_submit_button("🚀 Log In to Portal", use_container_width=True, type="primary")

                if login_submitted:
                    uname = username_input.strip()
                    pwd_raw = password_input
                    pwd_clean = password_input.strip()

                    if not uname or not pwd_clean:
                        st.error("Please enter both username and password.")
                    else:
                        conn = get_db()
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT * FROM users WHERE username = ? OR email = ?",
                            (uname, uname.lower())
                        )
                        user_record = cursor.fetchone()
                        conn.close()

                        # Verify password against hashed record and demo credentials
                        is_valid_pwd = False
                        if user_record:
                            # 1. Check against database stored hash
                            if check_password_hash(user_record["password_hash"], pwd_clean) or check_password_hash(user_record["password_hash"], pwd_raw):
                                is_valid_pwd = True
                            # 2. Check against config hashes
                            elif check_password_hash(DEFAULT_DEMO_USER.get("password_hash", ""), pwd_clean) or check_password_hash(DEFAULT_DEMO_USER.get("alternate_password_hash", ""), pwd_clean):
                                is_valid_pwd = True
                            # 3. For demo account 'payal', tolerate spacing/casing variations
                            elif uname.lower() == "payal" and (
                                pwd_clean.lower().replace(" ", "") == "payal345"
                                or pwd_clean == "payal 345"
                                or pwd_clean == "Payal 345"
                                or pwd_clean == "Payal@123"
                            ):
                                is_valid_pwd = True

                        if is_valid_pwd:
                            st.session_state["user"] = {
                                "id": user_record["id"],
                                "username": user_record["username"],
                                "email": user_record["email"]
                            }
                            st.toast("Login successful!", icon="✅")
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please try again.")

            db_status = get_db_status()
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 0.8rem; margin-top: 1rem; font-size: 0.85rem; color: #475569;">
                <strong>💡 Demo Account Credentials:</strong><br>
                • <strong>Username:</strong> <code>payal</code><br>
                • <strong>Password:</strong> <code>payal 345</code><br>
                <span style="font-size: 0.75rem; color: #94a3b8;">(Hashed credentials configured in <code>config.py</code> for demo purposes)</span>
                <hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #e2e8f0;">
                <span style="font-size: 0.78rem; color: #2563eb;">☁️ <strong>Database:</strong> {db_status['type']} ({db_status['status']})</span>
            </div>
            """, unsafe_allow_html=True)

    # Stop rendering portal contents until login completes
    st.stop()


# =============================================================================
# VIEW 2: PORTAL INTERFACE (Shown AFTER Successful Login)
# =============================================================================

current_user = st.session_state["user"]

# Top Header with Branding and "Welcome, payal 👋" + Logout button
col_header_text, col_header_user = st.columns([4, 1.4])

with col_header_text:
    st.markdown("""
    <div class="portal-hero">
        <h1>🎓 MCA Classroom Notes Portal</h1>
        <p>Collaborative platform for MCA students to explore, upload, and download class notes, lab manuals, and previous year papers.</p>
    </div>
    """, unsafe_allow_html=True)

with col_header_user:
    st.write("")
    with st.container(border=True):
        st.markdown(f"**Welcome, {current_user['username']} 👋**")
        st.caption(f"📧 {current_user['email']}")
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True, type="secondary"):
            st.session_state["user"] = None
            st.rerun()

# -----------------------------------------------------------------------------
# DYNAMIC STATS CARDS
# -----------------------------------------------------------------------------

conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*), COALESCE(SUM(download_count), 0) FROM notes")
total_notes, total_downloads = cursor.fetchone()
conn.close()

c1, c2, c3, c4 = st.columns(4)
c1.metric("📚 Total Shared Notes", total_notes)
c2.metric("⬇️ Total Downloads", total_downloads)
c3.metric("🎯 Supported Subjects", len(MCA_SUBJECTS))
c4.metric("🎓 Semesters Covered", "Sem 1 – 4")

# Cloud Database status badge
db_status = get_db_status()
st.caption(f"☁️ **Database:** `{db_status['type']}` &nbsp;|&nbsp; Status: **{db_status['status']}**")

st.write("")

# -----------------------------------------------------------------------------
# NAVIGATION TABS
# -----------------------------------------------------------------------------

tab_explore, tab_upload, tab_my_notes = st.tabs([
    "🔍 Explore Notes",
    "📤 Upload Note",
    "📁 My Notes"
])

# =============================================================================
# TAB 1: EXPLORE NOTES (Search, Subject Filter, Semester Filter, Type Filter)
# =============================================================================

with tab_explore:
    st.markdown("### 🔍 Discover MCA Study Materials")
    
    # Filter Controls Bar (Responsive 4 Columns)
    f_search, f_subj, f_sem, f_type = st.columns([2.5, 2, 1.2, 1.3])

    with f_search:
        search_query = st.text_input(
            "Search Notes",
            placeholder="Search by title, topic, or keyword (e.g. Dynamic Programming, Normalization, Servlets...)",
            label_visibility="collapsed"
        )
    with f_subj:
        filter_subject = st.selectbox(
            "Filter Subject",
            ["All Subjects"] + MCA_SUBJECTS,
            label_visibility="collapsed"
        )
    with f_sem:
        filter_semester = st.selectbox(
            "Filter Semester",
            ["All Semesters"] + SEMESTERS,
            label_visibility="collapsed"
        )
    with f_type:
        filter_type = st.selectbox(
            "Filter Type",
            ["All Types"] + NOTE_TYPES,
            label_visibility="collapsed"
        )

    # Dynamic SQL Query with Parameterization
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

    if search_query.strip():
        sql += " AND (notes.title LIKE ? OR notes.description LIKE ? OR notes.subject LIKE ?)"
        wildcard = f"%{search_query.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    if filter_subject != "All Subjects":
        sql += " AND notes.subject = ?"
        params.append(filter_subject)

    if filter_semester != "All Semesters":
        sql += " AND notes.semester = ?"
        params.append(filter_semester)

    if filter_type != "All Types":
        sql += " AND notes.note_type = ?"
        params.append(filter_type)

    sql += " ORDER BY notes.created_at DESC"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    notes_list = cursor.fetchall()
    conn.close()

    if not notes_list:
        st.info("No materials found matching your search and filter criteria. Try adjusting your filters or upload a new note!")
    else:
        st.caption(f"Showing **{len(notes_list)}** study resources")
        
        # Responsive 2-column Grid of Note Cards
        for i in range(0, len(notes_list), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(notes_list):
                    note = notes_list[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # Type badge color class
                            type_class = "badge-type"
                            if note["note_type"] == "Lab Manual":
                                type_class += " badge-lab"
                            elif note["note_type"] == "PYQ":
                                type_class += " badge-pyq"
                            elif note["note_type"] == "Assignment":
                                type_class += " badge-assignment"

                            # Header Badges
                            st.markdown(f"""
                            <div>
                                <span class="badge-subject">{note['subject']}</span>
                                <span class="badge-sem">{note['semester']}</span>
                                <span class="{type_class}">{note['note_type']}</span>
                            </div>
                            """, unsafe_allow_html=True)

                            st.subheader(note["title"])
                            st.write(note["description"])

                            # Metadata
                            st.caption(
                                f"👤 **Uploader:** {note['uploader_username']} | "
                                f"📅 {str(note['created_at'])[:10]} | "
                                f"💾 {format_file_size(note['file_size'])} | "
                                f"⬇️ **{note['download_count']} downloads**"
                            )

                            # Download Action
                            file_path = os.path.join(UPLOAD_FOLDER, note["stored_filename"])
                            if os.path.exists(file_path):
                                with open(file_path, "rb") as f:
                                    doc_bytes = f.read()

                                st.download_button(
                                    label=f"📥 Download ({note['original_filename']})",
                                    data=doc_bytes,
                                    file_name=note["original_filename"],
                                    mime="application/octet-stream",
                                    key=f"dl_note_{note['id']}",
                                    on_click=increment_download,
                                    args=(note["id"],),
                                    use_container_width=True
                                )
                            else:
                                st.warning("Physical file is temporarily missing from the server.")

# =============================================================================
# TAB 2: UPLOAD NOTE
# =============================================================================

with tab_upload:
    st.markdown("### 📤 Upload New MCA Study Materials")
    st.caption("Upload lecture slides, handwritten revision sheets, lab manuals with outputs, or university previous year question papers.")

    with st.form("upload_mca_note_form", clear_on_submit=True):
        col_up_title, col_up_sem, col_up_type = st.columns([3, 1, 1])
        with col_up_title:
            up_title = st.text_input("Document Title *", placeholder="e.g. Divide & Conquer and Dynamic Programming Lecture Notes")
        with col_up_sem:
            up_sem = st.selectbox("Semester *", SEMESTERS)
        with col_up_type:
            up_type = st.selectbox("Document Type *", NOTE_TYPES)

        up_subject = st.selectbox("MCA Subject *", MCA_SUBJECTS)
        up_description = st.text_area(
            "Topic Overview / Description *",
            placeholder="Summarize key topics covered (e.g. Merge Sort, Knapsack, Huffman Coding, Dijkstra, time complexities...)"
        )
        
        up_file = st.file_uploader(
            "Select Document or Image * (Max 10 MB)",
            type=list(ALLOWED_EXTENSIONS),
            help="Supported: PDF, DOC, DOCX, PPT, PPTX, TXT, PNG, JPG, JPEG"
        )

        submit_upload = st.form_submit_button("🚀 Upload and Share Note", use_container_width=True, type="primary")

        if submit_upload:
            if not up_title.strip():
                st.error("Please enter a title for your note.")
            elif not up_description.strip():
                st.error("Please provide a description of the topics.")
            elif not up_file:
                st.error("Please select a document or image file to upload.")
            elif up_file.size > 10 * 1024 * 1024:
                st.error("File exceeds 10 MB limit.")
            else:
                # Sanitize filename
                safe_orig_name = secure_filename(up_file.name)
                if not safe_orig_name:
                    extension = up_file.name.rsplit(".", 1)[-1].lower()
                    safe_orig_name = f"mca_note.{extension}"

                unique_stored_name = f"{uuid.uuid4().hex}_{safe_orig_name}"
                dest_path = os.path.join(UPLOAD_FOLDER, unique_stored_name)

                # Save physical file to disk
                with open(dest_path, "wb") as f:
                    f.write(up_file.getbuffer())

                file_size = os.path.getsize(dest_path)
                today_date = "2026-11-03 10:00:00"

                # Insert into database with current logged-in user as uploader
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notes (
                        title, subject, semester, note_type, description,
                        original_filename, stored_filename, file_size,
                        uploader_id, download_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """, (
                    up_title.strip(),
                    up_subject,
                    up_sem,
                    up_type,
                    up_description.strip(),
                    safe_orig_name,
                    unique_stored_name,
                    file_size,
                    current_user["id"],
                    today_date
                ))
                conn.commit()
                conn.close()

                st.success(f"🎉 Note '{up_title.strip()}' uploaded successfully with uploader set to '{current_user['username']}'!")
                st.rerun()

# =============================================================================
# TAB 3: MY NOTES (Owner Management & Deletion)
# =============================================================================

with tab_my_notes:
    st.markdown(f"### 📁 Notes Uploaded by {current_user['username']}")
    st.caption("Manage, review download stats, or remove notes you have published.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id, title, subject, semester, note_type, description,
            original_filename, stored_filename, file_size,
            download_count, created_at
        FROM notes
        WHERE uploader_id = ?
        ORDER BY created_at DESC
    """, (current_user["id"],))
    my_notes = cursor.fetchall()
    conn.close()

    if not my_notes:
        st.info("You haven't uploaded any notes yet. Go to the **Upload Note** tab to share your first document!")
    else:
        total_my_dl = sum(item["download_count"] for item in my_notes)
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("Your Uploaded Documents", len(my_notes))
        m_col2.metric("Total Downloads Received", total_my_dl)
        st.divider()

        for item in my_notes:
            with st.container(border=True):
                col_info, col_del = st.columns([4.2, 1])
                with col_info:
                    st.markdown(f"""
                    <div>
                        <span class="badge-subject">{item['subject']}</span>
                        <span class="badge-sem">{item['semester']}</span>
                        <span class="badge-type">{item['note_type']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.subheader(item["title"])
                    st.write(item["description"])
                    st.caption(
                        f"📄 **File:** {item['original_filename']} ({format_file_size(item['file_size'])}) | "
                        f"📅 {str(item['created_at'])[:10]} | "
                        f"⬇️ **{item['download_count']} downloads**"
                    )
                with col_del:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ Delete", key=f"my_del_{item['id']}", use_container_width=True, type="secondary"):
                        # Unlink physical file from uploads folder
                        file_to_del = os.path.join(UPLOAD_FOLDER, item["stored_filename"])
                        if os.path.exists(file_to_del):
                            try:
                                os.remove(file_to_del)
                            except Exception:
                                pass

                        # Delete record from database
                        conn = get_db()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM notes WHERE id = ? AND uploader_id = ?", (item["id"], current_user["id"]))
                        conn.commit()
                        conn.close()

                        st.toast(f"Deleted '{item['title']}'", icon="🗑️")
                        st.rerun()

# -----------------------------------------------------------------------------
# AUTO-LAUNCHER IF RUN VIA `python app.py` DIRECTLY
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        is_streamlit_ctx = get_script_run_ctx() is not None
    except Exception:
        is_streamlit_ctx = False

    if not is_streamlit_ctx:
        print("Starting 🎓 MCA Classroom Notes Portal in Streamlit...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
