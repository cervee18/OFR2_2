from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create the db instance
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SECRET_KEY'] = 'your_secret_key'
    
    # Initialize the db with the app
    db.init_app(app)
    
    # Import and register blueprints
    from app.routes.main_routes import main
    from app.routes.client_routes import clients
    from app.routes.visit_routes import visits
    from app.routes.trip_routes import trips
    
    app.register_blueprint(main)
    app.register_blueprint(clients)
    app.register_blueprint(visits)
    app.register_blueprint(trips)
    
    return app