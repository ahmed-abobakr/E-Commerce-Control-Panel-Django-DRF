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
    categories_name = ['Fashoin', "Phone", "Health & Beauity", "Televisions", "Baby Products", "Supermarket",
                       "Computing", "Sporting", "Gaming", "Others"]
    categories = []
    for _ in range(n):
        name = fake.word().capitalize()
        category = Category.objects.create(name=random.choice(categories_name))
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
    products_names = ["Slim Fit Jeans", "Leather Jacket", "Cotton T-Shirt", "Summer Dress", "Sports Sneakers",
                      "Wool Scarf", "Baseball Cap", "Formal Blazer", "Denim Skirt", "Running Shorts", "iPhone 14 Pro",
                      "Samsung Galaxy S23", "Xiaomi Redmi Note 12", "Infinix Hot 30", "Huawei Nova Y90", "Google Pixel 7",
                      "Phone Tripod Stand", "Wireless Earbuds", "Fast Charging Adapter", "Silicone Phone Case", "Vitamin C Serum",
                      "Face Moisturizer", "Beard Oil", "Electric Toothbrush", "Aloe Vera Gel", "Herbal Shampoo", "Sunscreen SPF 50",
                      "Lip Balm Set", "Hair Straightener", "Facial Cleanser", "Samsung 55-inch 4K TV", "LG OLED Smart TV",
                      "Sony Bravia 50-inch", "TCL Android TV 43-inch", "Hisense 32-inch LED TV", "TV Wall Mount Bracket", "Universal Remote Control",
                      "TV Sound Bar", "HDMI Cable 3m", "TV Cover Dust Proof", "Newborn Diapers Pack", "Baby Wipes Sensitive", "Baby Stroller 3-in-1",
                      "Baby Milk Bottle", "Baby Body Wash", "Infant Car Seat", "Pacifier Set", "High Chair for Feeding", "Baby Monitor Camera",
                      "Cotton Baby Blanket", "Long Grain Rice 5kg", "Sunflower Cooking Oil", "Granulated Sugar 2kg", "Bottled Drinking Water", "Black Tea Bags",
                      "Tomato Paste Cans", "Laundry Detergent 3L", "Toilet Paper Rolls", "Spaghetti Pack", "Table Salt 500g","Dell Inspiron Laptop",
                      "Logitech Wireless Mouse", "Mechanical Gaming Keyboard", "USB-C Hub 6-in-1", "External Hard Drive 1TB", "MacBook Pro M2", "Webcam 1080p HD",
                      "27-inch Monitor", "Desktop Cooling Fan", "Portable SSD 500GB", "Men's Running Shoes", "Dumbbell Set 20kg", "Yoga Mat Non-slip", "Basketball Size 7",
                      "Football Jersey", "Cycling Helmet", "Skipping Rope", "Tennis Racket", "Resistance Bands", "Swimming Goggles", "PlayStation 5 Console",
                      "Xbox Series X", "Nintendo Switch OLED", "Gaming Headset RGB", "Gaming Chair Recliner", "PS5 DualSense Controller", "Gaming Desk LED",
                      "Fortnite V-Bucks Card", "Gaming Mousepad XXL", "Steam Gift Card 50$", "Portable Air Purifier", "Rechargeable Torch", "Wall Clock Modern",
                      "Electric Kettle", "Mini Sewing Machine", "Smart Watch Band", "USB Rechargeable Fan", "Digital Thermometer", "Water Bottle Stainless Steel", 
                      "LED Strip Light 5m"]
    products = []
    for _ in range(n):
        product = Product.objects.create(
            title=random.choice(products_names),
            description=fake.text(max_nb_chars=100),
            price=round(random.uniform(10.0, 999.9), 2),
            stock_count=random.randint(70, 100),
            category=random.choice(categories),
            brand = fake.text(max_nb_chars=20),
            created_by= employee
            
        )
        products.append(product)
    return products    

#Populate Orders
def create_orders(products, customers, n = 100):
    employee = Employee.objects.get(role="Customer_Service")
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
            address = customer.address1,
            created_by= employee
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
