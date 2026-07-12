import os
from dotenv import load_dotenv
from flask import Flask
from models import db

load_dotenv()

ELEMENTS = [
    "Energy", "Holy", "Earth", "Death", "Agony", "Drown",
    "Fire", "Ice", "Life Drain", "Mana Drain", "Physical"
]


def create_app():
    app = Flask(__name__)
    APP_VERSION = "1.0.0"

    @app.context_processor
    def inject_app_version():
        return {"app_version": APP_VERSION}
    
    database_url = os.getenv("DATABASE_URL", "sqlite:///tibia_pt.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-me"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_pre_ping": True,
            "pool_recycle": 280,
        },
    )

    db.init_app(app)

    from routes import bp
    app.register_blueprint(bp)

    @app.context_processor
    def inject_globals():
        return {"ELEMENTS": ELEMENTS}

    with app.app_context():
        db.create_all()

    return app
