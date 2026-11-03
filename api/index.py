import os
import sys

# Add project root and student-notes-portal to Python module search path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "student-notes-portal"))

# Import the Flask application instance
from app import app
