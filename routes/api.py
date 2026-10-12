from flask import Blueprint, jsonify, request
from services.tasks import get_task, create_task, process_order, update_task_priority, list_tasks, PRIORITY_REASON
from services.users import get_user
from utils.errors import AppError, ValidationError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code

@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_route(task_id):
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValidationError("request body", "must be a JSON object")
    if "priority" not in data:
        raise ValidationError("priority", "is required")
    return jsonify(update_task_priority(task_id, data["priority"]))

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    values = request.args.getlist("priority")
    if not values:
        return jsonify(list_tasks())
    if len(values) > 1:
        raise ValidationError("priority", "must be provided at most once")
    raw = values[0]
    if not (raw.isascii() and raw.isdigit()):
        raise ValidationError("priority", PRIORITY_REASON)
    try:
        priority = int(raw)
    except ValueError:
        raise ValidationError("priority", PRIORITY_REASON) from None
    return jsonify(list_tasks(priority))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json()
    if "priority" in data:
        task = create_task(data["title"], data["user_id"], data["priority"])
    else:
        task = create_task(data["title"], data["user_id"])
    return jsonify(task), 201

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))
