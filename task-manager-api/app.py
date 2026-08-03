from datetime import datetime, timezone

from flask import Flask
from flask_cors import CORS

from config import settings
from config.logging_config import configure_logging
from database import db
from middlewares.error_handler import register_error_handlers
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp

configure_logging()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['DEBUG'] = settings.DEBUG
app.config['JWT_EXPIRATION_SECONDS'] = settings.JWT_EXPIRATION_SECONDS

CORS(app, origins=settings.ALLOWED_ORIGINS)
db.init_app(app)
register_error_handlers(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)

@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.now(timezone.utc))}

@app.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=settings.DEBUG, host='0.0.0.0', port=5000)
