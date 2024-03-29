import click
from flask.cli import FlaskGroup, with_appcontext

from server import create_flask_app
from server.extensions import db, guard
from server.models import users


app = create_flask_app()
cli = FlaskGroup(create_app=create_flask_app)


@app.cli.command("create-db")
@with_appcontext
def create_db():
    db.create_all()
    db.session.commit()
    print("Created database structure")


@app.cli.command("create-admin")
@click.argument("user")
@click.argument("pword")
def create_admin(user, pword):
    new_user = users.User(
        username=user,
        email=f"{user}@pymap-localhost",
        password=guard.hash_password(pword),
        roles="admin",
    )
    db.session.add(new_user)
    db.session.commit()
    ctx_str = f"\nCreated User:\nUser: {user}\nEmail: {user}@pymap-localhost\nPassword: {pword}\nRoles: {'admin'}\n======="
    print(ctx_str)


@app.cli.command("create-user")
@click.argument("user")
@click.argument("email")
@click.argument("password")
@click.option("-r", "--roles", "roles", default="operator")
def create_user(user, email, password, roles):
    new_user = users.User(
        username=user, email=email, password=guard.hash_password(password), roles=roles
    )
    db.session.add(new_user)
    db.session.commit()
    ctx_str = f"\nCreated User:\nUser: {user}\nEmail: {email}\nPassword: {password}\nRoles: {roles}\n======="
    print(ctx_str)


if __name__ == "__main__":
    cli()
