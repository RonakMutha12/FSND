import unittest
import json

from flask_sqlalchemy import SQLAlchemy

from models import setup_db, Question
from src.api import app


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = app
        self.client = app.test_client()
        self.database_name = "trivia_test"
        self.database_path = "postgresql:///trivia_test"
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.drop_all()

    def test_get_questions(self):
        response = self.client.get("/questions", follow_redirects=True)
        self.assertEqual(len(json.loads(response.data).get("questions")), 10)
        self.assertEqual(response.status_code, 200)

    def test_get_questions_pagination(self):
        response = self.client.get("/questions?page=1", follow_redirects=True)
        self.assertEqual(len(json.loads(response.data).get("questions")), 10)
        self.assertEqual(response.status_code, 200)

    def test_get_categories(self):
        response = self.client.get("/categories", follow_redirects=True)
        self.assertEqual(len(json.loads(response.data).get("categories")), 6)
        self.assertEqual(response.status_code, 200)

    def test_delete_question(self):
        question_id = Question.query.first().id
        response = self.client.delete(
            f"/questions/{question_id }", follow_redirects=True
        )
        self.assertEqual(json.loads(response.data).get("delete"), question_id)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f"/questions/{id}", follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_create_question(self):
        data = {
            "question": "What is the distance to the Moon in kilo meters?",
            "answer": "384400",
            "category": 1,
            "difficulty": 1,
        }
        headers = {"Content-Type": "application/json"}
        response = self.client.post(
            "/questions", data=json.dumps(data), headers=headers
        )
        self.assertEqual(response.status_code, 200)

    def test_search_question(self):
        data = {"searchTerm": "soccer"}
        headers = {"Content-Type": "application/json"}
        response = self.client.post(
            "/questions/search", data=json.dumps(data), headers=headers
        )
        query_response = Question.query.filter(
            Question.question.like(f"%{data.get('searchTerm')}%")
        ).all()
        total_questions = len(query_response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(json.loads(response.data).get("questions")), total_questions
        )

    def test_quiz_question(self):
        previous_questions = [1, 2]
        data = {
            "previous_questions": previous_questions,
            "quiz_category": {"type": "click", "id": 0},
        }
        headers = {"Content-Type": "application/json"}
        response = self.client.post("/quizzes", data=json.dumps(data), headers=headers)
        self.assertEqual(response.status_code, 200)
        assert (
            json.loads(response.data).get("question").get("id")
            not in previous_questions
        )


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
