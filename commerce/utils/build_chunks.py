# admin_ai/management/commands/build_admin_chunks.py
from django.core.management.base import BaseCommand
from django.db import connection
from products.models import Product
from categories.models import Category
from orders.models import Order, OrderItems
from customers.models import Customer
from employees.models import Employee
from commerce.services.embeddings import get_embedding


def ins(cur, etype, eid, source, text):
    if not text: return
    print("before get embedding")
    emb = get_embedding(text)
    cur.execute("""
      INSERT INTO admin_chunk (entity_type, entity_id, source, text, embedding)
      VALUES (%s, %s, %s, %s, %s::vector)
    """, [etype, eid, source, text, f"[{','.join(map(str, emb))}]"])
    
def insert_product_chunks(product):
    with connection.cursor() as cur:
        print("with connection in of insert product chunks")
            # Products
        try:
            p = Product.objects.select_related("category","created_by").get(title=product['title'], brand=product['brand'],
                                                                            price=product['price'], stock_count=product['stock_count'], rating=product['rating'])    
            base = f"Product: {p.title} | Brand: {p.brand} | Category: {p.category.name} | Price: {p.price} | Stock: {p.stock_count} | Rating: {p.rating}"
            ins(cur, "product", p.id, "product.header", base)  # :contentReference[oaicite:16]{index=16}
            ins(cur, "product", p.id, "product.description", p.description or "")  # :contentReference[oaicite:17]{index=17}
        except Exception as e:
            print(f"insert product chunk error: {e}")
    return "Product Admin chunks built."


def insert_category_chunks(category):
    with connection.cursor() as cur:
        print("with connection in of insert product chunks")
            # Categories
        try:
            c = Category.objects.get(name=category.name, parent_id=category.parent_id)    
            cat_txt = f"Category: {c.name} | parent_id={c.parent_id}"
            ins(cur, "category", c.id, "category.meta", cat_txt)  # :contentReference[oaicite:18]{index=18}
        except Exception as e:
            print(f"insert Category chunk error: {e}")
    return "Category Admin chunks built." 

def insert_order_and_items_chunks(order):
    with connection.cursor() as cur:
        print("with connection in of insert product chunks")
        print(f"order is: {order}")
            # Orders + Items
        try:
            o = Order.objects.select_related("customer").get(status=order['status'], sub_total=order['sub_total'],discount_total=order['discount_total'],
                                                             tax_total=order['tax_total'], shipping_price=order['shipping_price'],grand_price=order['grand_price'],
                                                             customer=order['customer']['id'], address=order['address'], payment_status=order['payment_status'], created_at=order['created_at'],
                                                             created_by=order['created_by'])   
            print(f"selectedOrder: {o}") 
            head = f"Order#{o.id} | status={o.status} | payment={o.payment_status} | grand={o.grand_price} | address={o.address}"
            ins(cur, "order", o.id, "order.snapshot", head)  # :contentReference[oaicite:19]{index=19}
            items = OrderItems.objects.filter(order=o).select_related("product")
            for it in items:
                itxt = f"Item: {getattr(it.product,'title','')} x{it.quantity}"
                ins(cur, "order", o.id, "order.item", itxt)  # :contentReference[oaicite:20]{index=20}
        except Exception as e:
            print(f"insert Order and Order Items chunk error: {e}")
    return "Order Admin chunks built."   

def insert_employee_chunks(employee):
    with connection.cursor() as cur:
        print("with connection in of insert product chunks")
            # Employees
        try:
            e = Employee.objects.get(first_name=employee['first_name'], last_name=employee['last_name'], phone=employee['phone'], role=employee['role'])    
            ins(cur, "employee", e.id, "employee.min",
                    f"Employee: {e.first_name} {e.last_name} | Role={e.role}")  # :contentReference[oaicite:22]{index=22}
        except Exception as e:
            print(f"insert employee chunk error: {e}")
    return "Employee Admin chunks built." 


def insert_customer_chunks(customer):
    with connection.cursor() as cur:
        print("with connection in of insert product chunks")
            # CUstomers
        try:
            cu = Customer.objects.get(first_name=customer['first_name'], last_name=customer['last_name'], phone=customer['phone'], address1=customer['address1'])    
            ins(cur, "customer", cu.id, "customer.min",
                    f"Customer: {cu.first_name} {cu.last_name}")  # :contentReference[oaicite:21]{index=21}
        except Exception as e:
            print(f"insert customer chunk error: {e}")
    return "Customer Admin chunks built."          
        

