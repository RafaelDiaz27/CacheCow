import uuid
from decimal import Decimal
from datetime import date
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session as flask_session,
)
from flask_login import current_user, login_required
from sqlalchemy import text
from extensions import db
from models import (
    Product,
    Cart,
    CartItem,
    UserSession,
    Order,
    OrderItem,
    Payment,
    PaymentMethod,
    OrderTracking,
)

shop_bp = Blueprint("shop", __name__)


def get_or_create_cart():
    """Return an active cart for the logged-in user or guest session."""
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(
            account_id=current_user.account_id, status="active"
        ).first()
        if not cart:
            cart = Cart(account_id=current_user.account_id, status="active")
            db.session.add(cart)
            db.session.commit()
        return cart

    token = flask_session.get("session_token")
    if not token:
        token = str(uuid.uuid4())
        flask_session["session_token"] = token

    sess = UserSession.query.filter_by(session_token=token).first()
    if not sess:
        sess = UserSession(session_id=str(uuid.uuid4()), session_token=token, is_guest=True)
        db.session.add(sess)
        db.session.commit()

    cart = Cart.query.filter_by(session_id=sess.session_id, status="active").first()
    if not cart:
        cart = Cart(session_id=sess.session_id, status="active")
        db.session.add(cart)
        db.session.commit()

    return cart


@shop_bp.route("/")
def index():
    sort = request.args.get("sort")
    query = Product.query.filter_by(is_active=True)

    if sort == "price_asc":
        query = query.order_by(Product.unit_price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.unit_price.desc())
    elif sort == "rating_desc":
        query = query.order_by(Product.average_rating.desc())

    products = query.all()
    return render_template("index.html", products=products)


@shop_bp.route("/search")
def search():
    q = request.args.get("q", "")
    if not q:
        return redirect(url_for("shop.index"))
    products = Product.query.filter(Product.name.ilike(f"%{q}%")).all()
    return render_template("product_list.html", products=products, query=q)


@shop_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)


@shop_bp.route("/cart")
def cart_view():
    cart = get_or_create_cart()
    items = cart.items
    total = sum(item.quantity * item.product.unit_price for item in items)
    return render_template("cart.html", cart=cart, items=items, total=total)


@shop_bp.route("/cart/add", methods=["POST"])
def cart_add():
    product_id = int(request.form["product_id"])
    quantity = int(request.form.get("quantity", 1))

    product = Product.query.get_or_404(product_id)
    if not product.is_active:
        flash("Product is not available.", "warning")
        return redirect(url_for("shop.index"))

    cart = get_or_create_cart()
    item = CartItem.query.filter_by(
        cart_id=cart.cart_id, product_id=product_id
    ).first()

    if item:
        item.quantity += quantity
    else:
        item = CartItem(
            cart_id=cart.cart_id,
            product_id=product_id,
            quantity=quantity,
        )
        db.session.add(item)

    db.session.commit()
    flash("Item added to cart.", "success")
    return redirect(url_for("shop.cart_view"))


@shop_bp.route("/cart/update", methods=["POST"])
def cart_update():
    cart = get_or_create_cart()
    for item in cart.items:
        field = f"quantity_{item.cart_item_id}"
        if field in request.form:
            new_qty = int(request.form[field])
            if new_qty <= 0:
                db.session.delete(item)
            else:
                item.quantity = new_qty
    db.session.commit()
    flash("Cart updated.", "success")
    return redirect(url_for("shop.cart_view"))


@shop_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = get_or_create_cart()
    items = cart.items
    total = sum(item.quantity * item.product.unit_price for item in items)

    def manual_order_fallback(used_pm_id):
        """Create an order without the stored procedure as a fallback."""
        if not cart.items:
            return None
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order = Order(
            account_id=current_user.account_id,
            status="processing",
            placed_at=db.func.now(),
            order_number=order_number,
            total_amount=Decimal(0),
        )
        db.session.add(order)
        db.session.flush()

        fallback_total = Decimal(0)
        for item in cart.items:
            line = Decimal(item.quantity) * Decimal(item.product.unit_price)
            fallback_total += line
            db.session.add(
                OrderItem(
                    order_id=order.order_id,
                    product_id=item.product_id,
                    qty=item.quantity,
                    unit_price_at_purchase=item.product.unit_price,
                    line_total=line,
                )
            )
            # decrement stock
            item.product.stock_qty = item.product.stock_qty - item.quantity

        order.total_amount = fallback_total
        db.session.add(
            Payment(order_id=order.order_id, payment_method_id=used_pm_id, amount=fallback_total)
        )
        CartItem.query.filter_by(cart_id=cart.cart_id).delete()
        cart.status = "ordered"
        db.session.commit()
        return order.order_id

    if request.method == "POST":
        if not cart.items:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("shop.cart_view"))

        # 1. Update User's Profile Address
        try:
            current_user.line_1 = request.form.get("line_1")
            current_user.city = request.form.get("city")
            current_user.province = request.form.get("province")
            current_user.postal_code = request.form.get("postal_code")
            current_user.country = request.form.get("country")
            db.session.commit()
        except Exception as e:
            print(f"Address update warning: {e}")
            db.session.rollback()

        # 2. Determine Payment Method ID
        payment_choice = request.form.get("payment_choice")
        final_pm_id = None

        if payment_choice == 'saved':
            final_pm_id = request.form.get("payment_method_id")
            if final_pm_id:
                final_pm_id = int(final_pm_id)
            else:
                flash("Please select a saved card.", "warning")
                return redirect(url_for("shop.checkout"))
        
        elif payment_choice == 'new':
            card_num = request.form.get("new_card_number", "0000")
            mask = f"••••{card_num[-4:]}"
            exp_str = request.form.get("new_expiry")
            exp_date = None
            if exp_str:
                try:
                    year, month = map(int, exp_str.split("-"))
                    exp_date = date(year, month, 1)
                except ValueError:
                    exp_date = None
            
            new_pm = PaymentMethod(
                account_id=current_user.account_id,
                type="card",
                card_number_mask=mask,
                expiry_date=exp_date
            )
            
            if request.form.get("save_card"):
                db.session.add(new_pm)
                db.session.commit() 
                final_pm_id = new_pm.payment_method_id
            else:
                db.session.add(new_pm)
                db.session.commit()
                final_pm_id = new_pm.payment_method_id
        
        # 3. Create Order
        try:
            result = db.session.execute(
                text("CALL sp_create_order_from_cart(:cart_id, :account_id, :pm_id)"),
                {
                    "cart_id": cart.cart_id,
                    "account_id": current_user.account_id,
                    "pm_id": final_pm_id,
                },
            )
            row = result.fetchone()
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            # If stored proc fails, we fall through to the manual fallback below
            # flash(f"Checkout failed: {exc}", "danger") 
            # return redirect(url_for("shop.checkout"))
            row = None

        order_id = None
        if row:
            order_id = getattr(row, "order_id", None)
            if order_id is None and len(row) > 0:
                order_id = row[0]

        if not order_id:
            latest = (
                Order.query.filter_by(account_id=current_user.account_id)
                .order_by(Order.order_id.desc())
                .first()
            )
            if latest:
                order_id = latest.order_id

        if not order_id:
            order_id = manual_order_fallback(final_pm_id)
            if not order_id:
                flash("There was a problem placing your order (no order id).", "danger")
                return redirect(url_for("shop.checkout"))

        # 4. Update Order Address
        order = Order.query.get(order_id)
        if order:
            order.line_1 = request.form["line_1"]
            order.city = request.form["city"]
            order.province = request.form["province"]
            order.postal_code = request.form["postal_code"]
            order.country = request.form["country"]
            db.session.commit()

        flash(f"Order placed! Order ID: {order_id}", "success")
        return redirect(url_for("shop.order_history"))

    payment_methods = PaymentMethod.query.filter_by(
        account_id=current_user.account_id
    ).all()
    
    # --- THIS WAS THE FIX ---
    # We pass BOTH 'items' and 'cart_items', and 'total' and 'cart_total'
    # to ensure compatibility regardless of which variable name your template uses.
    return render_template(
        "checkout.html",
        cart=cart,
        items=items,
        cart_items=items, 
        total=total,      
        cart_total=total, 
        payment_methods=payment_methods,
    )


@shop_bp.route("/orders")
@login_required
def order_history():
    orders = (
        Order.query.filter_by(account_id=current_user.account_id)
        .order_by(Order.placed_at.desc())
        .all()
    )
    return render_template("order_history.html", orders=orders)


@shop_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(
        order_id=order_id, account_id=current_user.account_id
    ).first_or_404()
    return render_template("order_detail.html", order=order)


@shop_bp.route("/payment-methods", methods=["GET", "POST"])
@login_required
def payment_methods():
    if request.method == "POST":
        pm_type = request.form.get("type") or "card"
        mask = request.form.get("card_number_mask") or "••••0000"
        exp = request.form.get("expiry_date")
        exp_date = None
        if exp:
            try:
                year, month = map(int, exp.split("-"))
                exp_date = date(year, month, 1)
            except ValueError:
                exp_date = None
        pm = PaymentMethod(
            account_id=current_user.account_id,
            type=pm_type,
            card_number_mask=mask,
            expiry_date=exp_date,
        )
        db.session.add(pm)
        db.session.commit()
        flash("Payment method added.", "success")
        return redirect(url_for("shop.payment_methods"))

    methods = PaymentMethod.query.filter_by(account_id=current_user.account_id).all()
    return render_template("payment_methods.html", methods=methods)


@shop_bp.route("/payment-methods/<int:pm_id>/delete", methods=["POST"])
@login_required
def delete_payment_method(pm_id):
    pm = PaymentMethod.query.filter_by(
        payment_method_id=pm_id, account_id=current_user.account_id
    ).first_or_404()
    db.session.delete(pm)
    db.session.commit()
    flash("Payment method removed.", "info")
    return redirect(url_for("shop.payment_methods"))