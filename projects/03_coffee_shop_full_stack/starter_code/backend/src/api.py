from flask import Flask, request, jsonify, abort
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()


# ROUTES


@app.route("/drinks", methods=["GET"])
def get_drinks():
    drinks_res = Drink.query.all()
    drinks = []
    for drink in drinks_res:
        drinks.append(drink.short())
    return jsonify({"success": True, "drinks": drinks})


@app.route("/drinks-detail", methods=["GET"])
@requires_auth(permission="get:drinks-detail")
def get_drink_details(data):
    drinks_res = Drink.query.all()
    drinks = []
    for drink in drinks_res:
        drinks.append(drink.long())
    return jsonify({"success": True, "drinks": drinks})


@app.route("/drinks", methods=["POST"])
@requires_auth(permission="post:drinks")
def create_drinks(data):
    data = json.loads(request.data)
    title = data.get("title")
    recipe = data.get("recipe")
    drink = Drink(title=title, recipe=json.dumps(recipe))
    drink.insert()
    return jsonify({"success": True, "drinks": drink.long()})


@app.route("/drinks/<id>", methods=["PATCH"])
@requires_auth(permission="patch:drinks")
def update_drinks(data, id):
    drink_id = request.view_args["id"]
    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if drink is None:
        abort(404)
    data = json.loads(request.data)
    title = data.get("title")
    recipe = data.get("recipe")
    if title:
        drink.title = title
    if recipe:
        drink.recipe = recipe
    drink.update()
    return jsonify({"success": True, "drinks": [drink.long()]})


@app.route("/drinks/<drink_id>", methods=["DELETE"])
@requires_auth(permission="delete:drinks")
def delete_drink(data, drink_id):
    drink_id = request.view_args["drink_id"]
    Drink.query.filter_by(id=drink_id).delete()
    return jsonify({"success": True, "delete": drink_id})


# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({"success": False, "error": 422, "message": "unprocessable"}), 422


@app.errorhandler(404)
def resource_not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "resource not found"}),
        404,
    )


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({"success": False, "error": 401, "message": "Not Authorized"}), 401
