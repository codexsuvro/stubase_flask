from flask import Flask
from app.config import Config
from app.extensions import (
    db,
    migrate,
    cors,
    api,
    jwt,
)
from app.seeds.seed import seed
import click
from datetime import UTC, datetime
from sqlalchemy import select, delete

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    from app import models
    
    migrate.init_app(app, db)
    cors.init_app(app)
    api.init_app(app)
    jwt.init_app(app)
    
    from app.models.token_blocklist import TokenBlocklist
    from app.auth.repository import get_user_by_id
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        
        # Explicitly reject tokens without the expected claims.
        jti = jwt_payload.get("jti")
        user_id = jwt_payload.get("sub")
        token_version = jwt_payload.get("token_version")

        if not jti or not user_id or token_version is None:
            return True

        # Reject tokens explicitly revoked during logout.
        statement = select(TokenBlocklist.id).where(
            TokenBlocklist.jti == jti
        )
        if db.session.scalar(statement) is not None:
            return True

        # Reject tokens belonging to missing or inactive accounts.
        user = get_user_by_id(user_id)
        if user is None or not user.is_active or not user.is_verified:
            return True

        # Reject all tokens issued before a password change.
        return token_version != user.token_version

    from app.auth.routes import blp as auth_blueprint
    api.register_blueprint(auth_blueprint)
    
    app.cli.add_command(seed)
    
    @app.cli.command("cleanup-revoked-tokens")
    def cleanup_revoked_tokens():
        """Delete blocklist entries for tokens that have expired."""
        statement = delete(TokenBlocklist).where(
            TokenBlocklist.expires_at < datetime.now(UTC)
        )

        try:
            result = db.session.execute(statement)
            deleted_count = result.rowcount or 0
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        click.echo(
            f"Removed {deleted_count} expired token record(s)."
        )

    return app