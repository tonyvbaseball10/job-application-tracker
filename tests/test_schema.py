import pathlib
import unittest


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = pathlib.Path(__file__).parents[1].joinpath("schema.sql").read_text(encoding="utf-8").lower()

    def test_all_required_tables_exist(self):
        for table in ("companies", "jobs", "applications", "contacts"):
            self.assertIn(f"create table {table}", self.schema)

    def test_json_and_foreign_keys_exist(self):
        self.assertGreaterEqual(self.schema.count(" json"), 2)
        self.assertGreaterEqual(self.schema.count("foreign key"), 3)


if __name__ == "__main__":
    unittest.main()

