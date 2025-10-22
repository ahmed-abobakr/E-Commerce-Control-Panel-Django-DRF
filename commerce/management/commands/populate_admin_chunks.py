from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from io import StringIO
from products.models import Product
from categories.models import Category
from orders.models import Order, OrderItems
from customers.models import Customer
from employees.models import Employee
from commerce.services.embeddings import get_embedding
from commerce.utils.build_chunks import ins

class Command(BaseCommand):
    help = "Build/refresh pgvector chunks for Admin RAG"

    def handle(self, *args, **kwargs):
        with connection.cursor() as cur:
            # Products
            for p in Product.objects.select_related("category","created_by").iterator():
                base = f"Product: {p.title} | Brand: {p.brand} | Category: {getattr(p.category,'name','')} | Price: {p.price} | Stock: {p.stock_count} | Rating: {p.rating}"
                ins(cur, "product", p.id, "product.header", base)  # :contentReference[oaicite:16]{index=16}
                ins(cur, "product", p.id, "product.description", p.description or "")  # :contentReference[oaicite:17]{index=17}

            # Categories
            for c in Category.objects.iterator():
                cat_txt = f"Category: {c.name} | parent_id={c.parent_id}"
                ins(cur, "category", c.id, "category.meta", cat_txt)  # :contentReference[oaicite:18]{index=18}

            # Orders + Items
            for o in Order.objects.select_related("customer").iterator():
                head = f"Order#{o.id} | status={o.status} | payment={o.payment_status} | grand={o.grand_price} | address={o.address}"
                ins(cur, "order", o.id, "order.snapshot", head)  # :contentReference[oaicite:19]{index=19}
                items = OrderItems.objects.filter(order=o).select_related("product")
                for it in items:
                    itxt = f"Item: {getattr(it.product,'title','')} x{it.quantity}"
                    ins(cur, "order", o.id, "order.item", itxt)  # :contentReference[oaicite:20]{index=20}

            # (Optional) Customers, Employees: فقط ملخّصات غير حساسة
            for cu in Customer.objects.iterator():
                ins(cur, "customer", cu.id, "customer.min",
                    f"Customer: {cu.first_name} {cu.last_name}")  # :contentReference[oaicite:21]{index=21}
            for e in Employee.objects.iterator():
                ins(cur, "employee", e.id, "employee.min",
                    f"Employee: {e.first_name} {e.last_name} | Role={e.role}")  # :contentReference[oaicite:22]{index=22}

            self.stdout.write(self.style.SUCCESS("Admin chunks built."))
         
         
""" def populate_admin_chunks():
    with connection.cursor() as cur:
            # Products
            for p in Product.objects.select_related("category","created_by").iterator():
                base = f"Product: {p.title} | Brand: {p.brand} | Category: {getattr(p.category,'name','')} | Price: {p.price} | Stock: {p.stock_count} | Rating: {p.rating}"
                ins(cur, "product", p.id, "product.header", base)  # :contentReference[oaicite:16]{index=16}
                ins(cur, "product", p.id, "product.description", p.description or "")  # :contentReference[oaicite:17]{index=17}

            # Categories
            for c in Category.objects.iterator():
                cat_txt = f"Category: {c.name} | parent_id={c.parent_id}"
                ins(cur, "category", c.id, "category.meta", cat_txt)  # :contentReference[oaicite:18]{index=18}

            # Orders + Items
            for o in Order.objects.select_related("customer").iterator():
                head = f"Order#{o.id} | status={o.status} | payment={o.payment_status} | grand={o.grand_price} | address={o.address}"
                ins(cur, "order", o.id, "order.snapshot", head)  # :contentReference[oaicite:19]{index=19}
                items = OrderItems.objects.filter(order=o).select_related("product")
                for it in items:
                    itxt = f"Item: {getattr(it.product,'title','')} x{it.quantity}"
                    ins(cur, "order", o.id, "order.item", itxt)  # :contentReference[oaicite:20]{index=20}

            # (Optional) Customers, Employees: فقط ملخّصات غير حساسة
            for cu in Customer.objects.iterator():
                ins(cur, "customer", cu.id, "customer.min",
                    f"Customer: {cu.first_name} {cu.last_name}")  # :contentReference[oaicite:21]{index=21}
            for e in Employee.objects.iterator():
                ins(cur, "employee", e.id, "employee.min",
                    f"Employee: {e.first_name} {e.last_name} | Role={e.role}")  # :contentReference[oaicite:22]{index=22}

    print("Admin chunks built.") """


""" def run():
    populate_admin_chunks()

if __name__ == '__main__':
    run() """