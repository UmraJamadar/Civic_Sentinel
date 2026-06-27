from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models.user_model import create_user, verify_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    create_user(data["username"], data["password"])
    return jsonify({"msg": "User Created"})

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    user = verify_user(data["username"], data["password"])
    if not user:
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=user["username"])
    return jsonify({"token": token})