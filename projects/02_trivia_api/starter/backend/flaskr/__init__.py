import json
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    cors = CORS(app, resources={r"*": {"origins": "*"}})
    # ROUTES

    """
  @TODO: Use the after_request decorator to set Access-Control-Allow
  """

    @app.after_request
    def add_cors_headers(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    """
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  """

    @app.route("/categories", methods=["GET"])
    def get_categories():
        response = Category.query.all()
        categories = []
        for category in response:
            categories.append(category.type)
        return jsonify({"success": True, "categories": categories})

    """
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  """

    @app.route("/questions", methods=["GET"])
    def get_questions(page=1):
        page = int(request.args.get("page")) if request.args.get("page") else 1
        per_page = 10
        max_per_page = 10
        error_out = False
        response = Question.query.paginate(page, per_page, error_out, max_per_page)
        questions = []
        categories = []
        current_category = None
        for question in response.items:
            questions.append(question.format())
            categories.append(
                Category.query.filter_by(id=question.category)
                .one_or_none()
                .type.lower()
            )
            current_category = question.category
        total_questions = Question.query.count()
        return jsonify(
            {
                "questions": questions,
                "totalQuestions": total_questions,
                "categories": categories,
                "currentCategory": current_category,
            }
        )

    """
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  """

    @app.route("/questions/<int:id>", methods=["DELETE"])
    def delete_question(id):
        id = int(request.view_args["id"])
        question = Question.query.filter_by(id=id).one_or_none()
        if question:
            question.delete()
        else:
            abort(404)
        return jsonify({"success": True, "delete": id})

    """
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  """

    @app.route("/questions", methods=["POST"])
    def create_question():
        data = json.loads(request.data)
        question = Question(**data)
        question.insert()
        return jsonify({"success": True})

    """
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  """

    @app.route("/questions/search", methods=["POST"])
    def search_question():
        data = json.loads(request.data)
        response = Question.query.filter(
            Question.question.like(f"%{data.get('searchTerm')}%")
        ).all()
        total_questions = len(response)
        questions = []
        current_category = None
        for question in response:
            questions.append(question.format())
            current_category = question.category
        return jsonify(
            {
                "questions": questions,
                "totalQuestions": total_questions,
                "currentCategory": current_category,
            }
        )

    """
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  """

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_questions_by_category(category_id):
        response = Question.query.filter_by(category=category_id).all()
        total_questions = len(response)
        questions = []
        current_category = None
        for question in response:
            questions.append(question.format())
            current_category = question.category
        return jsonify(
            {
                "questions": questions,
                "totalQuestions": total_questions,
                "currentCategory": current_category,
            }
        )

    """
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  """

    @app.route("/quizzes", methods=["POST"])
    def quiz_question():
        data = json.loads(request.data)
        quiz_category = data.get("quiz_category")
        previous_questions = data.get("previous_questions")
        category_id = quiz_category.get("type")
        if category_id != "click":
            category = Category.query.filter_by(type=category_id).one_or_none().id
            questions = Question.query.filter_by(category=category).all()
        else:
            questions = Question.query.all()
        questions = list(
            filter(lambda question: question.id not in previous_questions, questions)
        )
        return jsonify(
            {"question": random.choice(questions).format() if questions else None}
        )

    """
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  """

    # Error Handling

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify({"success": False, "error": 400, "message": "Bad Request"}),
            400,
        )

    @app.errorhandler(404)
    def resource_not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "Resource Not Found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify(
                {"success": False, "error": 422, "message": "Unprocessable Entity"}
            ),
            422,
        )

    @app.errorhandler(500)
    def server_error(error):
        return (
            jsonify({"success": False, "error": 500, "message": "Server Error"}),
            500,
        )

    return app
