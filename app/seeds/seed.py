from flask.cli import with_appcontext
import click

from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.utils.security import hash_password


@click.command("seed")
@with_appcontext
def seed():
    # --------------------------
    # Seed Roles
    # --------------------------
    roles = ["ADMIN", "FACULTY", "STUDENT"]

    for role_name in roles:
        role = Role.query.filter_by(role_name=role_name).first()

        if not role:
            db.session.add(Role(role_name=role_name))

    db.session.commit()

    # --------------------------
    # Seed Admin
    # --------------------------
    admin = User.query.filter_by(email="admin@stubase.com").first()

    if admin:
        click.echo("Admin already exists.")
        return

    admin_role = Role.query.filter_by(role_name="ADMIN").first()

    admin = User(
        username="admin",
        email="admin@stubase.com",
        password_hash=hash_password("Admin@123"),
        role_id=admin_role.id,
        is_active=True,
        is_verified=True,
    )

    db.session.add(admin)
    db.session.commit()

    click.echo("Database seeded successfully.")