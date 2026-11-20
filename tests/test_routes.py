import unittest
from unittest.mock import patch

import app as tracker


class RouteSmokeTests(unittest.TestCase):
    def setUp(self):
        tracker.app.config.update(TESTING=True, SECRET_KEY="test")
        self.client = tracker.app.test_client()

    def test_dashboard_renders(self):
        stats = {"companies": 2, "jobs": 2, "applications": 1, "contacts": 1, "interviews": 0, "offers": 0}
        with patch.object(tracker, "fetch_one", return_value=stats), patch.object(tracker, "fetch_all", side_effect=[[], []]):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Application dashboard", response.data)

    def test_all_list_pages_render(self):
        for path in ("/companies", "/jobs", "/applications", "/contacts"):
            with self.subTest(path=path), patch.object(tracker, "fetch_all", return_value=[]):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_job_match_renders_ranked_result(self):
        jobs = [{
            "job_id": 1,
            "job_title": "Software Developer",
            "job_type": "Full-time",
            "company_name": "TechCorp",
            "requirements": '["Python", "SQL", "Flask"]',
        }]
        with patch.object(tracker, "fetch_all", return_value=jobs):
            response = self.client.post("/job-match", data={"skills": "Python, SQL, Flask"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"100%", response.data)
        self.assertIn(b"Software Developer", response.data)


if __name__ == "__main__":
    unittest.main()

