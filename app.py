import os
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_sqlalchemy import SQLAlchemy

# ---------------- APP CONFIGURATION ----------------


load_dotenv()

app = Flask(__name__)

database_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///shopmate.db"
)

# Support PostgreSQL connection URLs
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "shopmate-development-key"
)

if database_url.startswith("sqlite"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False}
    }

db = SQLAlchemy(app)



# ---------------- PRODUCT DATABASE ----------------

class Product(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    category = db.Column(db.String(50))

    price = db.Column(db.Float, nullable=False)

    stock = db.Column(db.Integer, nullable=False)

    min_stock = db.Column(db.Integer, default=5)

    received_date = db.Column(db.Date, default=date.today)

    expiry_date = db.Column(db.Date, nullable=True)

    @property
    def status(self):

        if not self.expiry_date:
            return "No expiry date"

        days_left = (self.expiry_date - date.today()).days

        if days_left < 0:
            return "Expired"

        elif days_left <= 2:
            return "Sell soon"

        else:
            return "Fresh"

# ---------------- BILL DATABASE ----------------

class Sale(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    total = db.Column(db.Float, nullable=False, default=0)

    items = db.relationship(
        "SaleItem",
        backref="sale",
        cascade="all, delete-orphan"
    )


class SaleItem(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    sale_id = db.Column(
        db.Integer,
        db.ForeignKey("sale.id"),
        nullable=False
    )

    product_id = db.Column(db.Integer)

    product_name = db.Column(db.String(100), nullable=False)

    unit_price = db.Column(db.Float, nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    subtotal = db.Column(db.Float, nullable=False)



# ---------------- DASHBOARD ----------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/dashboard")
def dashboard():

    items = Product.query.all()

    total_products = len(items)

    low_stock = [
        p for p in items
        if p.stock <= p.min_stock
    ]

    expired = [
        p for p in items
        if p.status == "Expired"
    ]

    sell_soon = [
        p for p in items
        if p.status == "Sell soon"
    ]

    return render_template(
        "dashboard.html",
        total_products=total_products,
        low_stock=low_stock,
        expired=expired,
        sell_soon=sell_soon
    )


# ---------------- VIEW PRODUCTS ----------------

@app.route("/products")
def products():

    items = Product.query.order_by(Product.name).all()

    return render_template(
        "products.html",
        products=items
    )


# ---------------- ADD PRODUCT ----------------

@app.route("/products/add", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        category = request.form.get("category", "").strip()

        expiry_raw = request.form.get("expiry_date", "").strip()

        try:

            price = float(request.form.get("price", ""))

            stock = int(request.form.get("stock", ""))

            min_stock = int(request.form.get("min_stock") or 5)

            expiry = (
                datetime.strptime(expiry_raw, "%Y-%m-%d").date()
                if expiry_raw else None
            )

        except ValueError:

            flash("Please enter valid product details.")

            return render_template("add_product.html")

        if not name or price <= 0 or stock < 0 or min_stock < 0:

            flash("Enter a valid name, positive price and valid stock.")

            return render_template("add_product.html")

        product = Product(
            name=name,
            category=category,
            price=price,
            stock=stock,
            min_stock=min_stock,
            expiry_date=expiry
        )

        db.session.add(product)

        db.session.commit()

        flash("Product added successfully!")

        return redirect(url_for("products"))

    return render_template("add_product.html")


# ---------------- EDIT PRODUCT ----------------

@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):

    product = db.get_or_404(Product, product_id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        category = request.form.get("category", "").strip()

        expiry_raw = request.form.get("expiry_date", "").strip()

        try:

            price = float(request.form.get("price", ""))

            stock = int(request.form.get("stock", ""))

            min_stock = int(request.form.get("min_stock") or 5)

            expiry = (
                datetime.strptime(expiry_raw, "%Y-%m-%d").date()
                if expiry_raw else None
            )

        except ValueError:

            flash("Please enter valid product details.")

            return render_template(
                "edit_product.html",
                product=product
            )

        if not name or price <= 0 or stock < 0 or min_stock < 0:

            flash("Enter a valid name, positive price and valid stock.")

            return render_template(
                "edit_product.html",
                product=product
            )

        product.name = name

        product.category = category

        product.price = price

        product.stock = stock

        product.min_stock = min_stock

        product.expiry_date = expiry

        db.session.commit()

        flash("Product updated successfully!")

        return redirect(url_for("products"))

    return render_template(
        "edit_product.html",
        product=product
    )


# ---------------- DELETE PRODUCT ----------------

@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):

    product = db.get_or_404(Product, product_id)

    db.session.delete(product)

    db.session.commit()

    flash("Product deleted successfully!")

    return redirect(url_for("products"))

# ---------------- BILLING SYSTEM ----------------

@app.route("/billing", methods=["GET", "POST"])
def billing():

    available_products = Product.query.filter(
        Product.stock > 0
    ).order_by(Product.name).all()

    if request.method == "POST":

        product_ids = request.form.getlist("product_id")
        quantities = request.form.getlist("quantity")

        if not product_ids or len(product_ids) != len(quantities):
            flash("Please select products and quantities.")
            return redirect(url_for("billing"))

        # Combine repeated products into one quantity
        order = {}

        try:
            for product_id, quantity in zip(product_ids, quantities):

                if not product_id or not quantity:
                    raise ValueError

                pid = int(product_id)
                qty = int(quantity)

                if qty < 1:
                    raise ValueError

                order[pid] = order.get(pid, 0) + qty

        except ValueError:
            flash("Please enter valid product quantities.")
            return redirect(url_for("billing"))

        # Check stock before creating the bill
        products_to_sell = []

        for pid, qty in order.items():

            product = db.session.get(Product, pid)

            if product is None:
                flash("One of the selected products was not found.")
                return redirect(url_for("billing"))

            if qty > product.stock:
                flash(
                    f"Not enough stock for {product.name}. "
                    f"Available stock: {product.stock}"
                )
                return redirect(url_for("billing"))

            products_to_sell.append((product, qty))

        # Create bill and reduce stock
        try:

            sale = Sale(total=0)

            db.session.add(sale)
            db.session.flush()

            bill_total = 0

            for product, qty in products_to_sell:

                subtotal = product.price * qty

                item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=qty,
                    subtotal=subtotal
                )

                db.session.add(item)

                product.stock -= qty

                bill_total += subtotal

            sale.total = bill_total

            db.session.commit()

            flash("Bill saved successfully!")

            return redirect(
            url_for("receipt", sale_id=sale.id)
            )

        except Exception:

            db.session.rollback()

            flash("Unable to save bill. Please try again.")

            return redirect(url_for("billing"))

    return render_template(
        "billing.html",
        products=available_products
    )

# ---------------- PRINTABLE RECEIPT ----------------

@app.route("/receipt/<int:sale_id>")
def receipt(sale_id):

    sale = db.get_or_404(Sale, sale_id)

    return render_template(
        "receipt.html",
        sale=sale
    )

# ---------------- BILL HISTORY ----------------

@app.route("/bill-history")
def bill_history():

    bills = Sale.query.order_by(
        Sale.created_at.desc()
    ).all()

    return render_template(
        "bill_history.html",
        bills=bills
    )
@app.route("/sales-report")
def sales_report():

    today = date.today()

    today_start = datetime.combine(today, datetime.min.time())
    tomorrow = today_start + timedelta(days=1)

    week_start_date = today - timedelta(days=today.weekday())
    week_start = datetime.combine(week_start_date, datetime.min.time())

    month_start_date = today.replace(day=1)
    month_start = datetime.combine(month_start_date, datetime.min.time())

    if today.month == 12:
        next_month_date = date(today.year + 1, 1, 1)
    else:
        next_month_date = date(today.year, today.month + 1, 1)

    next_month = datetime.combine(next_month_date, datetime.min.time())

    today_bills = Sale.query.filter(
        Sale.created_at >= today_start,
        Sale.created_at < tomorrow
    ).all()

    week_bills = Sale.query.filter(
        Sale.created_at >= week_start,
        Sale.created_at < tomorrow
    ).all()

    month_bills = Sale.query.filter(
        Sale.created_at >= month_start,
        Sale.created_at < next_month
    ).all()

    today_sales = sum(bill.total for bill in today_bills)
    week_sales = sum(bill.total for bill in week_bills)
    month_sales = sum(bill.total for bill in month_bills)

    items_sold = sum(
        item.quantity
        for bill in today_bills
        for item in bill.items
    )

    recent_bills = Sale.query.order_by(
        Sale.created_at.desc()
    ).limit(10).all()

    return render_template(
        "sales_report.html",
        today_sales=today_sales,
        week_sales=week_sales,
        month_sales=month_sales,
        today_bills_count=len(today_bills),
        week_bills_count=len(week_bills),
        month_bills_count=len(month_bills),
        items_sold=items_sold,
        recent_bills=recent_bills
    )


# ---------------- RUN APPLICATION ----------------


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
