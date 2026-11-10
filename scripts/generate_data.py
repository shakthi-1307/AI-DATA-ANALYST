
import os
import random
from datetime import date, datetime, timedelta, time

import psycopg
from dotenv import load_dotenv

load_dotenv()

random.seed(42)

# -----------------------------
# DATABASE CONNECTION
# -----------------------------

conn = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

print("Connected to PostgreSQL!")

# -----------------------------
# SAMPLE BUSINESS DATA
# -----------------------------

first_names = [
    "Arun", "Rahul", "Priya", "Ananya", "Karthik",
    "Sneha", "Vikram", "Meera", "Aditya", "Divya"
]

last_names = [
    "Sharma", "Kumar", "Reddy", "Patel", "Iyer",
    "Singh", "Nair", "Gupta", "Rao", "Verma"
]

locations = [
    ("Chennai", "Tamil Nadu"),
    ("Bangalore", "Karnataka"),
    ("Mumbai", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Hyderabad", "Telangana"),
    ("Pune", "Maharashtra"),
    ("Kochi", "Kerala"),
    ("Kolkata", "West Bengal"),
    ("Jaipur", "Rajasthan"),
    ("Ahmedabad", "Gujarat")
]

categories = {
    "Electronics": ("Headphones", "Keyboard", "Monitor",
                    "Mouse", "Smartphone"),
    "Fashion": ("T-Shirt", "Jeans", "Jacket",
                "Shoes", "Watch"),
    "Home & Kitchen": ("Mixer", "Cookware", "Lamp",
                       "Vacuum Cleaner", "Chair"),
    "Books": ("Python Book", "Novel", "Science Book",
              "History Book", "Notebook"),
    "Sports": ("Football", "Basketball", "Yoga Mat",
               "Badminton Racket", "Gym Bag")
}

payment_methods = ["UPI", "Credit Card", "Debit Card", "Net Banking"]

order_statuses = [
    "delivered", "shipped", "confirmed",
    "pending", "cancelled", "returned"
]

status_weights = [60, 12, 10, 6, 8, 4]

# -----------------------------
# GENERATE CUSTOMERS
# -----------------------------

customer_ids = []

with conn.cursor() as cur:

    for i in range(1000):

        name = (
            f"{random.choice(first_names)} "
            f"{random.choice(last_names)}"
        )

        city, state = random.choice(locations)

        signup_date = date.today() - timedelta(
            days=random.randint(30, 1000)
        )

        email = f"customer{i + 1}@example.com"

        cur.execute(
            """
            INSERT INTO customers
            (name, email, city, state, signup_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING customer_id
            """,
            (name, email, city, state, signup_date)
        )

        customer_ids.append(cur.fetchone()[0])

print("1,000 customers created!")

# -----------------------------
# GENERATE PRODUCTS
# -----------------------------

product_ids = []
product_prices = {}

with conn.cursor() as cur:

    for i in range(100):

        category = random.choice(list(categories.keys()))
        product_type = random.choice(categories[category])

        product_name = f"{product_type} Model {i + 1}"
        sku = f"SKU-{i + 1:04d}"

        price_ranges = {
            "Electronics": (500, 50000),
            "Fashion": (300, 8000),
            "Home & Kitchen": (200, 15000),
            "Books": (100, 2000),
            "Sports": (300, 10000)
        }

        low, high = price_ranges[category]
        price = round(random.uniform(low, high), 2)

        cur.execute(
            """
            INSERT INTO products
            (sku, product_name, category, price)
            VALUES (%s, %s, %s, %s)
            RETURNING product_id
            """,
            (sku, product_name, category, price)
        )

        product_id = cur.fetchone()[0]

        product_ids.append(product_id)
        product_prices[product_id] = price

print("100 products created!")

# -----------------------------
# GENERATE ORDERS AND ITEMS
# -----------------------------

item_records = []
payment_records = []

start_date = date.today() - timedelta(days=365)
end_date = date.today()

with conn.cursor() as cur:

    for i in range(10000):

        customer_id = random.choice(customer_ids)

        days_after_start = random.randint(
            0, (end_date - start_date).days
        )

        order_day = start_date + timedelta(days=days_after_start)

        order_datetime = datetime.combine(
            order_day,
            time(
                random.randint(8, 22),
                random.randint(0, 59)
            )
        )

        status = random.choices(
            order_statuses,
            weights=status_weights,
            k=1
        )[0]

        cur.execute(
            """
            INSERT INTO orders
            (customer_id, order_date, status)
            VALUES (%s, %s, %s)
            RETURNING order_id
            """,
            (customer_id, order_datetime, status)
        )

        order_id = cur.fetchone()[0]

        # Generate 1-4 items per order
        number_of_items = random.randint(1, 4)

        order_total = 0

        for _ in range(number_of_items):

            product_id = random.choice(product_ids)
            quantity = random.randint(1, 3)

            unit_price = product_prices[product_id]

            line_total = quantity * unit_price

            discount = round(
                line_total * random.uniform(0, 0.15), 2
            )

            order_total += line_total - discount

            item_records.append((
                order_id,
                product_id,
                quantity,
                unit_price,
                discount
            ))

        # Payment status based on order status
        payment_status = {
            "delivered": "completed",
            "shipped": "completed",
            "confirmed": "completed",
            "pending": "pending",
            "cancelled": "failed",
            "returned": "refunded"
        }[status]

        payment_date = order_datetime + timedelta(
            hours=random.randint(0, 72)
        )

        payment_records.append((
            order_id,
            round(order_total, 2),
            random.choice(payment_methods),
            payment_status,
            payment_date,
            f"TXN-{i + 1:06d}"
        ))

    # Insert all order items
    cur.executemany(
        """
        INSERT INTO order_items
        (order_id, product_id, quantity, unit_price, discount_amount)
        VALUES (%s, %s, %s, %s, %s)
        """,
        item_records
    )

    # Insert all payments
    cur.executemany(
        """
        INSERT INTO payments
        (order_id, amount, payment_method,
         payment_status, payment_date, transaction_reference)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        payment_records
    )

conn.commit()

print("\nData generation completed!")

# -----------------------------
# VERIFY RECORD COUNTS
# -----------------------------

with conn.cursor() as cur:

    tables = [
        "customers",
        "products",
        "orders",
        "order_items",
        "payments"
    ]

    print("\nDATABASE SUMMARY")

    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]

        print(f"{table}: {count}")

conn.close()

print("\nDatabase connection closed.")
