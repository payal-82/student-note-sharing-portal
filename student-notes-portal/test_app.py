"""
Comprehensive automated test suite for Student Notes Sharing Portal.
Tests all authentication, note uploads, search/filtering, downloads,
authorization, deletion, and file handling using Flask test client.
"""

import os
import io
import unittest
import tempfile
import sqlite3
import shutil

# Ensure app imports cleanly
import app as portal_app


class StudentNotesPortalTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        portal_app.app.config["TESTING"] = True
        portal_app.app.config["WTF_CSRF_ENABLED"] = False
        
        # Create a temporary directory for database and uploads during test run
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_notes.db")
        self.uploads_path = os.path.join(self.test_dir, "test_uploads")
        os.makedirs(self.uploads_path, exist_ok=True)
        
        # Override paths in app
        portal_app.DATABASE_PATH = self.db_path
        portal_app.UPLOAD_FOLDER = self.uploads_path
        portal_app.app.config["UPLOAD_FOLDER"] = self.uploads_path
        
        # Initialize schema
        portal_app.init_db()
        
        self.client = portal_app.app.test_client()

    def tearDown(self):
        # Clean up temporary test files
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def register(self, username, email, password, confirm_password):
        return self.client.post("/register", data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": confirm_password
        }, follow_redirects=True)

    def login(self, login_input, password):
        return self.client.post("/login", data={
            "login_input": login_input,
            "password": password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def upload_file(self, title, subject, description, filename, content_bytes):
        data = {
            "title": title,
            "subject": subject,
            "description": description,
            "file": (io.BytesIO(content_bytes), filename)
        }
        return self.client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)

    # ---------------------------------------------------------
    # AUTHENTICATION TESTS
    # ---------------------------------------------------------

    def test_user_registration_and_login(self):
        """Test successful registration and login."""
        # 1. Register Alice
        res = self.register("alice", "alice@example.com", "password123", "password123")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Account created successfully", res.data)

        # 2. Login Alice
        res = self.login("alice", "password123")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome back, alice", res.data)

        # 3. Logout Alice
        res = self.logout()
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"logged out successfully", res.data)

    def test_registration_validation(self):
        """Test validation rules for user registration."""
        # Short password
        res = self.register("bob", "bob@example.com", "123", "123")
        self.assertIn(b"Password must be at least 6 characters long", res.data)

        # Passwords mismatch
        res = self.register("bob", "bob@example.com", "password123", "mismatch123")
        self.assertIn(b"Passwords do not match", res.data)

        # Duplicate username/email
        self.register("carol", "carol@example.com", "password123", "password123")
        res = self.register("carol", "other@example.com", "password123", "password123")
        self.assertIn(b"Username or email already exists", res.data)

    def test_login_invalid_credentials(self):
        """Test rejection of invalid credentials."""
        self.register("david", "david@example.com", "password123", "password123")
        res = self.login("david", "wrongpassword")
        self.assertIn(b"Invalid credentials", res.data)

    # ---------------------------------------------------------
    # ACCESS CONTROL TESTS
    # ---------------------------------------------------------

    def test_protected_routes_redirect_unauthenticated_users(self):
        """Ensure /upload and /my-notes require authentication."""
        res = self.client.get("/upload", follow_redirects=True)
        self.assertIn(b"Please log in to access this page", res.data)

        res = self.client.get("/my-notes", follow_redirects=True)
        self.assertIn(b"Please log in to access this page", res.data)

    # ---------------------------------------------------------
    # NOTE UPLOAD & FILE VALIDATION TESTS
    # ---------------------------------------------------------

    def test_note_upload_and_disk_persistence(self):
        """Test note upload with allowed extension and verify file on disk."""
        self.register("student1", "student1@example.com", "password123", "password123")
        self.login("student1", "password123")

        dummy_content = b"%PDF-1.4 Data Structures Lecture Notes"
        res = self.upload_file(
            title="Data Structures & Algorithms Cheatsheet",
            subject="DAA (Design & Analysis of Algorithms)",
            description="Complete summary of Trees, Graphs, and Hashmaps.",
            filename="dsa_notes.pdf",
            content_bytes=dummy_content
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Your study note has been uploaded and published successfully", res.data)
        self.assertIn(b"Data Structures &amp; Algorithms Cheatsheet", res.data)

        # Check DB
        db = portal_app.get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM notes WHERE title = ?", ("Data Structures & Algorithms Cheatsheet",))
        note = cursor.fetchone()
        self.assertIsNotNone(note)
        self.assertEqual(note["subject"], "DAA (Design & Analysis of Algorithms)")
        self.assertEqual(note["original_filename"], "dsa_notes.pdf")
        self.assertEqual(note["file_size"], len(dummy_content))
        
        # Check physical file on disk
        stored_file_path = os.path.join(self.uploads_path, note["stored_filename"])
        self.assertTrue(os.path.exists(stored_file_path))
        with open(stored_file_path, "rb") as f:
            self.assertEqual(f.read(), dummy_content)
        db.close()

    def test_invalid_file_extension_rejected(self):
        """Test that disallowed file types (.exe, .sh) are rejected."""
        self.register("student2", "student2@example.com", "password123", "password123")
        self.login("student2", "password123")

        res = self.upload_file(
            title="Malicious Script",
            subject="DAA (Design & Analysis of Algorithms)",
            description="Testing executable rejection",
            filename="script.exe",
            content_bytes=b"MZ malicious content"
        )
        self.assertIn(b"Invalid file type", res.data)

    # ---------------------------------------------------------
    # HOMEPAGE EXPLORE, SEARCH & SUBJECT FILTER TESTS
    # ---------------------------------------------------------

    def test_search_and_filter(self):
        """Test home feed search by query and subject filter."""
        self.register("prof", "prof@example.com", "password123", "password123")
        self.login("prof", "password123")

        # Upload note 1: TOC
        self.upload_file("DFA and NFA Models", "TOC (Theory of Computation)", "Automata and pumping lemma", "toc.pdf", b"toc pdf")
        # Upload note 2: Operating Systems
        self.upload_file("Operating Systems Deadlocks", "Operating Systems", "Deadlock avoidance algorithms", "os.pdf", b"os pdf")

        # Test index displays both
        res = self.client.get("/")
        self.assertIn(b"DFA and NFA Models", res.data)
        self.assertIn(b"Operating Systems Deadlocks", res.data)

        # Test subject filter: TOC only
        res = self.client.get("/?subject=TOC+(Theory+of+Computation)")
        self.assertIn(b"DFA and NFA Models", res.data)
        self.assertNotIn(b"Operating Systems Deadlocks", res.data)

        # Test text search: 'Deadlocks'
        res = self.client.get("/?q=Deadlocks")
        self.assertNotIn(b"DFA and NFA Models", res.data)
        self.assertIn(b"Operating Systems Deadlocks", res.data)

    # ---------------------------------------------------------
    # DOWNLOAD & COUNTER TESTS
    # ---------------------------------------------------------

    def test_download_increments_counter(self):
        """Verify note download serves file with original filename and increments counter."""
        self.register("uploader", "uploader@example.com", "password123", "password123")
        self.login("uploader", "password123")

        sample_bytes = b"DBMS Normalization PDF content"
        self.upload_file("Normalization Notes", "DBMS (Database Management Systems)", "Detailed 1NF-BCNF explanation", "dbms_notes.pdf", sample_bytes)

        db = portal_app.get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, download_count FROM notes WHERE title = 'Normalization Notes'")
        note = cursor.fetchone()
        note_id = note["id"]
        self.assertEqual(note["download_count"], 0)
        db.close()

        # Download note
        res = self.client.get(f"/download/{note_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, sample_bytes)
        self.assertIn("attachment; filename=dbms_notes.pdf", res.headers.get("Content-Disposition", ""))

        # Check counter increment
        db = portal_app.get_db()
        cursor = db.cursor()
        cursor.execute("SELECT download_count FROM notes WHERE id = ?", (note_id,))
        updated_note = cursor.fetchone()
        self.assertEqual(updated_note["download_count"], 1)
        db.close()

    # ---------------------------------------------------------
    # AUTHORIZATION & DELETION TESTS
    # ---------------------------------------------------------

    def test_owner_deletion_and_unauthorized_deletion(self):
        """Test that only the owner can delete their note and physical file is cleaned up."""
        # 1. User A uploads a note
        self.register("user_a", "a@example.com", "password123", "password123")
        self.login("user_a", "password123")
        self.upload_file("User A Java Lab", "Advanced Java (Lab)", "JDBC and Servlets", "java.pdf", b"java data")

        db = portal_app.get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, stored_filename FROM notes WHERE title = 'User A Java Lab'")
        note = cursor.fetchone()
        note_id = note["id"]
        stored_file_path = os.path.join(self.uploads_path, note["stored_filename"])
        self.assertTrue(os.path.exists(stored_file_path))
        db.close()

        self.logout()

        # 2. User B tries to delete User A's note -> Access Denied
        self.register("user_b", "b@example.com", "password123", "password123")
        self.login("user_b", "password123")
        res = self.client.post(f"/delete/{note_id}", follow_redirects=True)
        self.assertIn(b"Access denied", res.data)
        self.assertTrue(os.path.exists(stored_file_path))  # File must still exist!

        self.logout()

        # 3. User A deletes their own note -> Success
        self.login("user_a", "password123")
        res = self.client.post(f"/delete/{note_id}", follow_redirects=True)
        self.assertIn(b"was deleted successfully", res.data)
        
        # File must be deleted from disk
        self.assertFalse(os.path.exists(stored_file_path))

        # Record must be deleted from DB
        db = portal_app.get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        self.assertIsNone(cursor.fetchone())
        db.close()


if __name__ == "__main__":
    unittest.main()

