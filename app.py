import os

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy.pool import NullPool
from werkzeug.security import generate_password_hash

from models import User, db


load_dotenv()


ELEMENTS = [
    "Energy",
    "Holy",
    "Earth",
    "Death",
    "Agony",
    "Drown",
    "Fire",
    "Ice",
    "Life Drain",
    "Mana Drain",
    "Physical",
]


def create_app():
    app = Flask(__name__)

    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///tibia_pt.db",
    )

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    engine_options = {
        "pool_pre_ping": True,
    }

    # Supabase Transaction Pooler / Vercel serverless
    if ":6543/" in database_url:
        engine_options["poolclass"] = NullPool
        engine_options["connect_args"] = {
            "prepare_threshold": None,
        }
    else:
        # SQLite local ou conexão PostgreSQL direta/session pooler
        engine_options["pool_recycle"] = 280

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-me"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS=engine_options,
    )

    db.init_app(app)

    from routes import bp

    app.register_blueprint(bp)

    @app.context_processor
    def inject_globals():
        version_path = os.path.join(app.root_path, "VERSION")

        if os.path.exists(version_path):
            with open(version_path, encoding="utf-8") as version_file:
                app_version = version_file.read().strip()
        else:
            app_version = "1.4.0"

        return {
            "ELEMENTS": ELEMENTS,
            "app_version": app_version,
        }

    with app.app_context():
        db.create_all()

        bootstrap_username = (
            os.getenv("INITIAL_ADMIN_USERNAME")
            or os.getenv("ADMIN_USERNAME")
        )

        bootstrap_password = (
            os.getenv("INITIAL_ADMIN_PASSWORD")
            or os.getenv("ADMIN_PASSWORD")
        )

        bootstrap_name = os.getenv(
            "INITIAL_ADMIN_NAME",
            "Administrador",
        )

        user_exists = db.session.scalar(
            db.select(User.id).limit(1)
        )

        if (
            not user_exists
            and bootstrap_username
            and bootstrap_password
        ):
            admin = User(
                name=bootstrap_name,
                username=bootstrap_username.strip().lower(),
                password_hash=generate_password_hash(
                    bootstrap_password
                ),
                role="admin",
                active=True,
            )

            db.session.add(admin)
            db.session.commit()

    return app