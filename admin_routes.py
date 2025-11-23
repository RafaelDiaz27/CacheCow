from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required, login_user, logout_user
from extensions import db, bcrypt
from models import Account, Product, Category

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_admin():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.products"))
        logout_user()

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = Account.query.filter_by(email=email).first()
        if user and user.role == "admin" and bcrypt.check_password_hash(
            user.password_hash, password
        ):
            login_user(user)
            flash("Logged in as admin.", "success")
            return redirect(url_for("admin.products"))
        flash("Admin credentials required.", "danger")
    return render_template("admin_login.html")


@admin_bp.route("/products")
@login_required
def products():
    require_admin()
    products = Product.query.order_by(Product.name).all()
    return render_template("admin_products.html", products=products)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    require_admin()
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        product = Product(
            name=request.form["name"],
            description=request.form.get("description"),
            unit_price=request.form.get("unit_price"),
            stock_qty=request.form.get("stock_qty"),
            is_active=bool(request.form.get("is_active")),
            category_id=request.form.get("category_id") or None,
        )
        db.session.add(product)
        db.session.commit()
        flash("Product created.", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin_product_form.html", categories=categories, product=None)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def product_edit(product_id):
    require_admin()
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        product.name = request.form["name"]
        product.description = request.form.get("description")
        product.unit_price = request.form.get("unit_price")
        product.stock_qty = request.form.get("stock_qty")
        product.is_active = bool(request.form.get("is_active"))
        product.category_id = request.form.get("category_id") or None
        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin_product_form.html", categories=categories, product=product)


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def product_delete(product_id):
    require_admin()
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("admin.products"))
