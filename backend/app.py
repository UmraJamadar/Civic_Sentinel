from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from config import *

from routes.auth_routes import auth_bp
from routes.complaint_routes import complaint_bp
from routes.admin_routes import admin_bp
from routes.location_routes import location_bp

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = JWT_SECRET
jwt = JWTManager(app)

# MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(complaint_bp, url_prefix="/complaint")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(location_bp, url_prefix="/location")

if __name__ == "__main__":
    app.run(debug=True)