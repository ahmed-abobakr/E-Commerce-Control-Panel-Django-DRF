from django.core.exceptions import PermissionDenied
from django.db import models
# products/services.py
from products.models import Product
from products.api.serializers import ProductSerializer
from categories.models import Category
from employees.api.services import get_employee
from commerce.utils.build_chunks import insert_product_chunks, delete_product_chunks
from commerce.services.rag import build_restock_prompt, search_admin_chunks

# -----------------------------
# Product CRUD services
# -----------------------------

def list_products():
    """Return all products"""
    return Product.objects.all()


def get_product(product_id):
    """Get one product by ID"""
    return Product.objects.filter(id=product_id).first()

def get_products_by_name_and_brand(request, name: str, brand: str = None) -> list:
    """
    Get products by name and brand (optional)
    Args:
        request: Django Request Object
        name: Product name (partial match)
        brand: Brand name (optional, partial match)

    Returns:
        multiple products 
    """
    print(f"getProductsByName and category: {name}")
    queryset = Product.objects.filter(
            models.Q(title__icontains=name))
    
    if brand:
        queryset = queryset.filter(brand__icontains=brand)

    return queryset


def create_product(request, validated_data):
    """
    Create product and insert chunks for RAG search.
    validated_data: dict containing serializer.validated_data
    """
    print(f"request User: {str(request.user.id).upper()}")
    employee = get_employee(request, request.user.id)
    print(f"request Employee Role: {employee.role}")
    role = employee.role
    print(f"request User Role: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager"}
    if role not in allowed_roles:
        raise PermissionDenied()
    print(f"request user role: {request.user}")
    product = Product.objects.create(**validated_data)
    try:
        print("service before insert product chunks")
        insert_product_chunks(product)  # Pass the model instance directly
        message = "Product chunks inserted successfully"
    except Exception as e:
        print(f"Error creating product: {e}")
        message = "Error building product chunks"
    return product


def update_product(request, product_id, validated_data):
    """Update an existing product"""
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager"}
    if role not in allowed_roles:
        raise PermissionDenied()
    product = get_product(product_id)
    if not product:
        return None
    for key, value in validated_data.items():
        setattr(product, key, value)
    product.save()
    try:
        delete_product_chunks(product_id)
        message = "Product chunks deleted successfully"
        insert_product_chunks(product)  # Pass the model instance directly
    except Exception as e:
        print(f"Error updating product chunks: {e}")
        message = "Error deleting product chunks"
    return product


def delete_product(request, product_id):
    """Delete product by ID"""
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager"}
    if role not in allowed_roles:
        raise PermissionDenied()
    product = get_product(product_id)
    if not product:
        return False
    product.delete()
    try:
        delete_product_chunks(product_id)
        message = "Product chunks deleted successfully"
    except Exception as e:
        print(f"Error deleting product chunks: {e}")
        message = "Error deleting product chunks"
    return True


# -----------------------------
# Restock Advisor logic
# -----------------------------

def get_restock_advice(request, category, threshold=50, k=10, q=None):
    """
    Generate restock advice for a given category.
    """
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager"}
    if role not in allowed_roles:
        return {"count": 0, "data": [], "advice": None, "message": "You are not allowed to call this function"}
    if not category:
        raise ValueError("category is required")
    
    q = q or f"restock candidates for category {category['name']}"
    print(f"restock advice servce category: {category}")

    # SQL pre-filter: low stock & high rating in category
    qs = (Product.objects
          .filter(category=category['id'], stock_count__lt=threshold)
          .values("id", "title", "stock_count", "price", "rating")
          .order_by("stock_count"))

    rows = list(qs)
    if not rows:
        return {"count": 0, "data": [], "advice": None}
    print(f"restock advice service rows: {rows}")

    # Semantic retrieval
    retrieved = search_admin_chunks(q, k=50, entity_type="product")

    # Prioritize items present in rows
    ids = {r["id"] for r in rows}
    ranked = [c for c in retrieved if c["entity_id"] in ids][:k]

    advice = build_restock_prompt(category['name'], rows, ranked)

    return {
        "count": len(rows),
        "filtered": rows[:50],
        "top_ranked": [
            {"product_id": c["entity_id"], "source": c["source"], "distance": c["distance"]}
            for c in ranked
        ],
        "advice": advice,
    }