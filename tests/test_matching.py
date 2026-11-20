import unittest

from app import calculate_matches, json_array, json_object, normalize_skills, optional_int


class MatchingTests(unittest.TestCase):
    def test_rank_and_percentages(self):
        jobs = [
            {"job_id": 1, "job_title": "Developer", "requirements": '["Python", "SQL", "Flask"]'},
            {"job_id": 2, "job_title": "Analyst", "requirements": '["Python", "SQL", "Tableau"]'},
        ]
        results = calculate_matches(jobs, "python, SQL, flask")
        self.assertEqual(results[0]["job_title"], "Developer")
        self.assertEqual(results[0]["percentage"], 100)
        self.assertEqual(results[1]["percentage"], 67)
        self.assertEqual(results[1]["missing"], ["Tableau"])

    def test_skills_are_case_insensitive_and_deduplicated(self):
        self.assertEqual(set(normalize_skills("Python, python\nSQL")), {"python", "sql"})

    def test_json_helpers(self):
        self.assertEqual(json_array("Python, SQL"), '["Python", "SQL"]')
        self.assertEqual(json_object('{"rounds": 2}'), '{"rounds": 2}')

    def test_optional_integer_validation(self):
        self.assertIsNone(optional_int("", "Salary"))
        self.assertEqual(optional_int("75000", "Salary"), 75000)
        with self.assertRaises(ValueError):
            optional_int("-1", "Salary")


if __name__ == "__main__":
    unittest.main()

