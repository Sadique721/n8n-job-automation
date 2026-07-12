import os
import sys
import shutil
import unittest
import sqlite3
import json

# Set test environment data directory before importing process_job
TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data_dir"))
os.environ["DATA_DIR"] = TEST_DATA_DIR

import process_job

class TestProcessJob(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Ensure clean test directory
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
        os.makedirs(TEST_DATA_DIR, exist_ok=True)
        
    @classmethod
    def tearDownClass(cls):
        # Cleanup test directory after run
        if os.path.exists(TEST_DATA_DIR):
            try:
                shutil.rmtree(TEST_DATA_DIR)
            except:
                pass
            
    def setUp(self):
        # Re-initialize directories and database before each test
        process_job.ensure_directories()
        process_job.init_db()
        
    def tearDown(self):
        # Clean up database file to start fresh
        db_path = process_job.get_path("Database/jobs.db")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except:
                pass

    def test_sanitize_filename(self):
        self.assertEqual(process_job.sanitize_filename("Google (Cloud Services)"), "Google_Cloud_Services")
        self.assertEqual(process_job.sanitize_filename("Amazon - Software Engineer!"), "Amazon_-_Software_Engineer")
        self.assertEqual(process_job.sanitize_filename("  Microsoft Corp  "), "Microsoft_Corp")

    def test_sanitize_for_pdf(self):
        # Test replacement of common Unicode characters
        self.assertEqual(process_job.sanitize_for_pdf("smart quote\u2019s"), "smart quote's")
        self.assertEqual(process_job.sanitize_for_pdf("en\u2013dash"), "en-dash")
        self.assertEqual(process_job.sanitize_for_pdf("em\u2014dash"), "em-dash")
        self.assertEqual(process_job.sanitize_for_pdf("bullet\u2022point"), "bullet*point")
        # Test fallback for entirely unsupported Unicode characters (e.g. Arabic or emojis)
        # Latin-1 fallback replaces unsupported characters with '?'
        self.assertEqual(process_job.sanitize_for_pdf("emoji \U0001F600"), "emoji ?")
        self.assertEqual(process_job.sanitize_for_pdf("arabic \u0625\u0646\u062c\u0644\u064a\u0632\u064a"), "arabic ???????")

    def test_init_db(self):
        db_path = process_job.get_path("Database/jobs.db")
        self.assertTrue(os.path.exists(db_path))
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check jobs table columns
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        self.assertIn("job_url", columns)
        self.assertIn("title", columns)
        self.assertIn("company", columns)
        self.assertIn("location", columns)
        self.assertIn("match_score", columns)
        self.assertIn("priority_score", columns)
        self.assertIn("contact_email", columns)
        
        # Check candidate_profile table columns
        cursor.execute("PRAGMA table_info(candidate_profile)")
        columns_cand = [row[1] for row in cursor.fetchall()]
        self.assertIn("id", columns_cand)
        self.assertIn("name", columns_cand)
        self.assertIn("email", columns_cand)
        self.assertIn("phone", columns_cand)
        
        conn.close()

    def test_save_candidate_profile(self):
        candidate_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1 234 567 890",
            "skills": ["Python", "SQL"],
            "programmingLanguages": ["Python"],
            "yearsExperience": 2.5
        }
        process_job.save_candidate_profile(candidate_data)
        
        db_path = process_job.get_path("Database/jobs.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, phone, years_experience FROM candidate_profile WHERE id='default_candidate'")
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Test User")
        self.assertEqual(row[1], "test@example.com")
        self.assertEqual(row[2], "+1 234 567 890")
        self.assertEqual(row[3], 2.5)

    def test_save_job_to_db(self):
        job_data = {
            "jobUrl": "https://example.com/job123",
            "title": "Software Engineer",
            "company": "Test Co",
            "jobLocation": "Bengaluru",
            "source": "LinkedIn",
            "description": "Test job description",
            "tags": "Python",
            "matchScore": 85
        }
        tailored_data = {
            "skillGap": "None",
            "experienceMatch": "Yes",
            "locationMatch": "Yes",
            "remoteMatch": "No",
            "salaryMatch": "N/A",
            "priorityScore": 90,
            "recommendation": "Apply",
            "matchSummary": "Good candidate match.",
            "tailoredBullets": ["Bullet 1", "Bullet 2"],
            "coverLetterOpener": "Dear Hiring Team,",
            "contactEmail": "jobs@example.com"
        }
        
        process_job.save_job_to_db(job_data, tailored_data)
        
        db_path = process_job.get_path("Database/jobs.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title, company, match_score, priority_score, contact_email FROM jobs WHERE job_url='https://example.com/job123'")
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Software Engineer")
        self.assertEqual(row[1], "Test Co")
        self.assertEqual(row[2], 85.0)
        self.assertEqual(row[3], 90.0)
        self.assertEqual(row[4], "jobs@example.com")

if __name__ == "__main__":
    unittest.main()
