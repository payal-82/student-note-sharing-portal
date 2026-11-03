"""
Configuration settings for MCA Classroom Notes Portal.
======================================================
NOTE: The default credentials below are for demo purposes only.
In production environments, credentials and secrets should be loaded from
secure environment variables or a vault.
"""

import os

# Neon PostgreSQL Database Connection URL
# Fallback to local SQLite if empty or unreachable
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_tDgwchG0AzP7@ep-morning-shadow-bee13hno-pooler.c-9.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

# Default demo student account
# Username: payal
# Password: payal 345 (also supports payal345)
# Stored securely as a Werkzeug scrypt hash (never plain-text)
DEFAULT_DEMO_USER = {
    "username": "payal",
    "email": "payal@mca.edu",
    # Werkzeug scrypt hash of 'payal 345'
    "password_hash": "scrypt:32768:8:1$HHNcgSR4HQYcLVE5$dbcb31db576a47577025a1176459b31acb479234accefc83bd849e696ffd689507a4eeabed65a7d21c62f7abbca5ed8aa5acd48f52ad15fef60323c52ea0e0f7",
    # Secondary hash for 'payal345' without spaces
    "alternate_password_hash": "scrypt:32768:8:1$fYPFVBRQIUwu14IA$29e12e2bfad95f2b2ad217ea3644b7fe595b7e073ee6a991b11404af1f7771ec00c5c20679c68c7e4efa3dee76241c3b02cb868e02e60cb40aad1dd2bbd82494"
}

SECRET_KEY = os.environ.get("SECRET_KEY", "mca-classroom-portal-key-2026")
