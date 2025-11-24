from extensions import bcrypt, db
from models import Account, Category, Product


def seed_defaults():
    """Insert a small set of demo data for fresh clones."""
    if Category.query.first():
        return

    admin = Account(
        email="admin@example.com",
        phone="555-000-0000",
        password_hash=bcrypt.generate_password_hash("admin123").decode("utf-8"),
        first_name="Admin",
        last_name="User",
        role="admin",
    )

    cpu = Category(name="CPUs", description="Processors for desktops and laptops")
    gpu = Category(name="GPUs", description="Graphics cards for gaming and workstations")

    products = [
        Product(
            category=cpu,
            name="Ryzen 7 7800X3D",
            description="8-core CPU with 3D V-Cache",
            unit_price=449.99,
            stock_qty=10,
            average_rating=4.8,
        ),
        Product(
            category=gpu,
            name="RTX 4070 Super",
            description="NVIDIA Ada Lovelace GPU with DLSS 3",
            unit_price=599.99,
            stock_qty=8,
            average_rating=4.7,
        ),
    ]

    db.session.add_all([admin, cpu, gpu, *products])
    db.session.commit()
