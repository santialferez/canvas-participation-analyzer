"""
Configuration settings for Canvas Participation Analyzer
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Canvas API Configuration
CANVAS_BASE_URL = "https://your-canvas-instance.edu/api/v1"
CANVAS_API_TOKEN = os.getenv("CANVAS_API_TOKEN", "")

# Course settings
COURSE_ID = 12345  # TODO: Update this with your course ID

# Professor identification (to exclude from student analysis)
PROFESSOR_NAMES = ["Professor Name"]
PROFESSOR_IDS = [54321]  # Add specific user IDs if known

# Date filtering for analysis
SEMESTER_START_DATE = "2025-02-15"  # Filter messages from this date onwards

# Default grading scheme
DEFAULT_GRADING_SCHEME = "tiered"

# Export settings
DEFAULT_EXPORT_FORMAT = "csv"
DEFAULT_OUTPUT_FILE = "participation_grades.csv"

# Analysis settings
EXCLUDE_PROFESSOR = True
INCLUDE_FORUMS = True
INCLUDE_MESSAGES = True

# Progress display settings
SHOW_PROGRESS = True
VERBOSE = False