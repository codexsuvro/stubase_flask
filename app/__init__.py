from flask import Flask
from app.config import Config
from app.extensions import (
    db,
    migrate,
    cors,
    api,
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    from app import models
    
    migrate.init_app(app, db)
    cors.init_app(app)
    api.init_app(app)
    
        
    return app