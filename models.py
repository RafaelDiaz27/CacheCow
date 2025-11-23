from datetime import datetime
from flask_login import UserMixin
from extensions import db


class Account(UserMixin, db.Model):
    __tablename__ = "account"

    account_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.String(50), default="customer")
    points_balance = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    addresses = db.relationship("Address", backref="account", lazy=True)
    carts = db.relationship("Cart", backref="account", lazy=True)
    orders = db.relationship("Order", backref="account", lazy=True)
    payment_methods = db.relationship("PaymentMethod", backref="account", lazy=True)
    reviews = db.relationship("Review", backref="account", lazy=True)

    def get_id(self):
        return str(self.account_id)


class Address(db.Model):
    __tablename__ = "address"

    address_id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.Integer, db.ForeignKey("account.account_id", ondelete="CASCADE")
    )
    line_1 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    province_state = db.Column(db.String(100))
    postal_code = db.Column(db.String(30))
    country = db.Column(db.String(100))
    is_default_shipping = db.Column(db.Boolean, default=False)


class Category(db.Model):
    __tablename__ = "category"

    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)

    products = db.relationship("Product", backref="category", lazy=True)


class Product(db.Model):
    __tablename__ = "product"

    product_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.category_id"))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock_qty = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    average_rating = db.Column(db.Numeric(3, 2), default=0)

    reviews = db.relationship("Review", backref="product", lazy=True)
    cart_items = db.relationship("CartItem", backref="product", lazy=True)
    order_items = db.relationship("OrderItem", backref="product", lazy=True)


class Review(db.Model):
    __tablename__ = "review"

    review_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.product_id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("account.account_id", ondelete="SET NULL"),
    )
    rating = db.Column(db.SmallInteger, nullable=False)
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserSession(db.Model):  # rename to avoid clash with flask.session
    __tablename__ = "session"

    session_id = db.Column(db.String(36), primary_key=True)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("account.account_id", ondelete="SET NULL"),
    )
    session_token = db.Column(db.String(255), unique=True)
    is_guest = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    carts = db.relationship("Cart", backref="session", lazy=True)


class Cart(db.Model):
    __tablename__ = "cart"

    cart_id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.account_id"))
    session_id = db.Column(
        db.String(36),
        db.ForeignKey("session.session_id", ondelete="SET NULL"),
    )
    status = db.Column(db.String(50), default="active")
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    items = db.relationship(
        "CartItem",
        backref="cart",
        lazy=True,
        cascade="all, delete-orphan",
    )


class CartItem(db.Model):
    __tablename__ = "cart_item"

    cart_item_id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(
        db.Integer,
        db.ForeignKey("cart.cart_id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.product_id"),
        nullable=False,
    )
    quantity = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    __tablename__ = "orders"

    order_id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("account.account_id", ondelete="SET NULL"),
    )
    postal_code = db.Column(db.String(30))
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    placed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="pending")
    order_number = db.Column(db.String(50), unique=True)
    province = db.Column(db.String(100))
    line_1 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))

    items = db.relationship("OrderItem", backref="order", lazy=True)
    tracking_events = db.relationship("OrderTracking", backref="order", lazy=True)
    payments = db.relationship("Payment", backref="order", lazy=True)


class OrderItem(db.Model):
    __tablename__ = "order_item"

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.product_id"),
        nullable=False,
    )
    qty = db.Column(db.Integer, nullable=False)
    unit_price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)


class OrderTracking(db.Model):
    __tablename__ = "order_tracking"

    order_tracking_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )
    status = db.Column(db.String(100))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)


class PaymentMethod(db.Model):
    __tablename__ = "payment_method"

    payment_method_id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey("account.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    type = db.Column(db.String(50))
    cvv = db.Column(db.String(10))
    expiry_date = db.Column(db.Date)
    card_number_mask = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship("Payment", backref="payment_method", lazy=True)


class Payment(db.Model):
    __tablename__ = "payment"

    payment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_method_id = db.Column(
        db.Integer,
        db.ForeignKey("payment_method.payment_method_id"),
    )
    amount = db.Column(db.Numeric(12, 2))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
