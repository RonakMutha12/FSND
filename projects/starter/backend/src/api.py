import json
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"*": {"origins": "*"}})

# ROUTES


@app.after_request
def add_cors_headers(response):
    # response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", 'Content-Type, Authorization')
    response.headers.add("Access-Control-Allow-Methods", 'GET, POST, PATCH, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


@app.route("/categories", methods=["GET"])
def get_categories():
    response = Category.query.all()
    categories = []
    for category in response:
        categories.append(category.type)
    return jsonify({"success": True, "categories": categories})


@app.route("/questions", methods=["GET"])
def get_questions(page=1):
    page = int(request.args.get("page")) if request.args.get("page") else 1
    per_page = 10
    max_per_page = 10
    error_out = False
    response = Question.query.paginate(page, per_page, error_out, max_per_page)
    questions = []
    categories = [each.type for each in Category.query.all()]
    current_category = []
    for question in response.items:
        questions.append(question.format())
    total_questions = Question.query.count()
    return jsonify(
        {
            "questions": questions,
            "totalQuestions": total_questions,
            "currentCategory": current_category,
            "categories": categories,
        }
    )


@app.route("/questions/<int:id>", methods=["DELETE"])
def delete_question(id):
    id = int(request.view_args["id"])
    question = Question.query.filter_by(id=id).one_or_none()
    if question:
        question.delete()
    else:
        abort(404)
    return jsonify({"success": True, "delete": id})


@app.route("/questions", methods=["POST"])
def create_question():
    data = request.json
    question = Question(**data)
    result = question.insert()
    total_questions = Question.query.count()
    return jsonify(
        {"success": True,
         "insert":result.id,
         "totalQuestions": total_questions
         }
    )


@app.route("/questions/search", methods=["POST"])
def search_question():
    data = json.loads(request.data)
    response = Question.query.filter(
        Question.question.like(f"%{data.get('searchTerm')}%")
    ).all()
    total_questions = len(response)
    questions = []
    current_category = set()
    for question in response:
        questions.append(question.format())
        current_category.add(question.category)
    return jsonify(
        {
            "questions": questions,
            "totalQuestions": total_questions,
            "currentCategory": list(current_category),
        }
    )


@app.route("/categories/<int:category_id>/questions", methods=["GET"])
def get_questions_by_category(category_id):
    response = Question.query.filter_by(category=str(category_id)).all()
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
        filter(
            lambda question: question.id not in previous_questions, questions
        )
    )
    return jsonify(
        {"question": random.choice(questions).format() if questions else None}
    )


# Error Handling


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": 400,
                    "message": "Bad Request"}), 400


@app.errorhandler(404)
def resource_not_found(error):
    return (
        jsonify({"success": False, "error": 404,
                 "message": "Resource Not Found"}),
        404,
    )


@app.errorhandler(422)
def unprocessable(error):
    return (
        jsonify({"success": False, "error": 422,
                 "message": "Unprocessable Entity"}),
        422,
    )


@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "error": 500,
                    "message": "Server Error"}), 500
