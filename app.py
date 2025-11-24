from flask import Flask
from config import Config
from extensions import db, bcrypt, login_manager
from models import Account
from auth_routes import auth_bp
from shop_routes import shop_bp
from admin_routes import admin_bp
from seed_data import seed_defaults


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Account.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp)

    # Auto-create tables and seed demo data for fresh clones.
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        with app.app_context():
            db.create_all()
            seed_defaults()

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
