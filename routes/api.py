from flask import Blueprint, jsonify, request
from services.tasks import get_task, create_task, process_order, update_task_priority, list_tasks, parse_priority_filter
from services.users import get_user
from utils.errors import AppError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code

@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_route(task_id):
    return jsonify(update_task_priority(task_id, request.get_json()))

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    return jsonify(list_tasks(parse_priority_filter(request.args.getlist("priority"))))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json()
    if "priority" in data:
        return jsonify(create_task(data["title"], data["user_id"], data["priority"])), 201
    return jsonify(create_task(data["title"], data["user_id"])), 201

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))
