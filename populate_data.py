import os
import django
import random
from faker import Faker

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'commerce.settings')  # adjust this path
django.setup()

# Import models
from categories.models import Category
from customers.models import Customer
from products.models import Product
from employees.models import Employee
from orders.models import Order, OrderItems

fake = Faker()

# Populate Categories
def create_categories(n=5):
    categories = []
    for _ in range(n):
        name = fake.word().capitalize()
        category = Category.objects.create(name=name)
        categories.append(category)
    return categories

# Populate Customers
def create_customers(n=10):
    customers = []
    for _ in range(n):
        customer = Customer.objects.create_user(
            username=fake.user_name(),
            email=fake.email(),
            password='123',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            address1=fake.address(),
            phone=fake.phone_number()
        )
        customers.append(customer)
    return customers    

# Populate Products
def create_products(categories, n=50):
    employee = Employee.objects.get(role="Customer_Service_Manager")
    products = []
    for _ in range(n):
        product = Product.objects.create(
            title=fake.text(max_nb_chars=20),
            description=fake.text(max_nb_chars=100),
            price=round(random.uniform(10.0, 999.9), 2),
            stock_count=random.randint(0, 100),
            category_id=random.choice(categories),
            brand = fake.text(max_nb_chars=20),
            created_by= employee
            
        )
        products.append(product)
    return products    

#Populate Orders
def create_orders(products, customers, n = 100):
    for _ in range(n):
        sub_total_value = round(random.uniform(10.0, 999.9), 2)
        shipping_price_value = random.randint(50, 100)
        grand_price_value = sub_total_value + (sub_total_value * 0.14) + shipping_price_value
        customer = random.choice(customers)
        order = Order.objects.create(
            status = random.choice(list(Order.ORDER_STATUS.keys())),
            sub_total = sub_total_value,
            tax_total = 0.14,
            shipping_price = shipping_price_value,
            grand_price = grand_price_value,
            payment_status = random.choice(list(Order.ORDER_PAYMENT.keys())),
            customer = customer,
            address = customer.address1
        )
        for _ in range(random.randrange(1, 5)):
            OrderItems.objects.create(
                product = random.choice(products),
                quantity = random.randint(1, 10),
                order = order
            )

# Run all
def run():
    print("Populating database...")
    categories = create_categories(10)
    customers = create_customers(20)
    products = create_products(categories, 50)
    create_orders(products, customers, 50)
    print("Done!")

if __name__ == '__main__':
    run()
