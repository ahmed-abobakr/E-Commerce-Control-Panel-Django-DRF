# services.py

from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum
from django.core.exceptions import PermissionDenied, ValidationError
from orders.models import Order, OrderItems
from customers.models import Customer
from products.models import Product
from products.api.services import update_product
from .serializers import OrderSerializer
from products.api.serializers import ProductSerializer
from employees.api.services import get_employee
from commerce.utils.build_chunks import insert_order_and_items_chunks, delete_order_chunks
from commerce.services.rag import (
    recommend_products_for_customer,
    build_recommendation_message,
    build_discount_message_for_customer,
    build_order_explain_prompt
)


# ------------------------------------------------------
# 🧩 ORDER SERVICE FUNCTIONS
# ------------------------------------------------------

def get_paginated_orders_with_products(request, queryset, page=None):
    """
    Build paginated response data for orders,
    including order detail and list of products per order.
    """
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager", "Customer_Service"}
    if role not in allowed_roles:
        raise PermissionDenied()
    from collections import defaultdict

    # Collect all unique order IDs sorted ascending
    order_ids = queryset.values_list('order_id', flat=True).distinct().order_by('id')

    # Fetch orders
    orders_qs = (
        Order.objects.filter(id__in=order_ids)
        .select_related('customer')
        .order_by('id')
    )

    # Apply pagination if provided
    paginated_orders = page if page is not None else orders_qs

    response_data = []
    for order in paginated_orders:
        order_detail = OrderSerializer(order).data
        product_ids = queryset.filter(order=order).values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids)
        products_list = ProductSerializer(products, many=True).data

        response_data.append({
            "order_detail": order_detail,
            "products": products_list
        })

    return response_data


def get_order_with_products(request, order_item):
    """
    Return a single order and its products.
    """
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager", "Customer_Service"}
    if role not in allowed_roles:
        raise PermissionDenied()
    order = order_item.order
    order_detail = OrderSerializer(order).data
    products = Product.objects.filter(orderitems__order=order)
    products_list = ProductSerializer(products, many=True).data

    return {
        "order_detail": order_detail,
        "products": products_list
    }


def get_order_by_id_with_products(request, order_id):
    """
    Return a single order and its products using order ID.
    """
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager", "Customer_Service"}
    if role not in allowed_roles:
        raise PermissionDenied()

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return {"error": "Order not found"}, 404

    order_detail = OrderSerializer(order).data
    products = Product.objects.filter(orderitems__order=order)
    products_list = ProductSerializer(products, many=True).data

    return {
        "order_detail": order_detail,
        "products": products_list
    }

def create_order_and_recommend(request, serializer):
    """
    Handle order creation and generate recommendations.
    """
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role: {role}")
    print(f"requestBody: {serializer.validated_data}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager", "Customer_Service"}
    if role not in allowed_roles:
        raise PermissionDenied()  
    serializer.is_valid(raise_exception=True)
    status = serializer.validated_data.get('status', Order.ORDER_FINISHED)
    if status not in Order.ORDER_STATUS:
        raise ValidationError(f"Invalid order status. Valid choices are: {list(Order.ORDER_STATUS.keys())}")

    order_items_data = serializer.validated_data.get("order_items", None)
    if order_items_data is not None:
        for item in order_items_data:
            product = item['product']
            if product.stock_count < item['quantity']:
                raise ValidationError(
                    f"Not enough stock for {product.name}. Available: {product.stock_count}"
                )
        for item in order_items_data:   
            print(f"order_item: {item}") 
            product = item['product']
            product.stock_count = product.stock_count - item['quantity']
            update_product(request, product.id, {'stock_count': product.stock_count})        
    order = serializer.save()
    
    
    response = OrderSerializer(order)
    insert_order_and_items_chunks(response.data)

    try:
        customer = Customer.objects.get(id=response.data['customer']['id'])
    except Customer.DoesNotExist:
        customer = None

    recs, context = recommend_products_for_customer(customer, k=6)
    response_data = response.data.copy()
    response_data["recommended_products"] = [r['title'] for r in recs]
    response_data["recommendation_message"] = build_recommendation_message(customer, recs, context)

    return response_data

def update_order(request, order_id, update_data):
    employee = get_employee(request, request.user.id)
    allowed_roles = {"Top_Manager", "Customer_Service_Manager", "Customer_Service"}

    if employee.role not in allowed_roles:
        raise PermissionDenied("You are not authorized to update orders")
    
    order = Order.objects.get(id=order_id)
    order_items_data = update_data.pop("order_items", None)
    if not order:
        return None
    for key, value in update_data.items():
        setattr(order, key, value)
    order.save()
    if order_items_data is not None:
        OrderItems.objects.filter(order=order).delete()
        # Validate stock before updating
        for item in order_items_data:
            product = Product.objects.get(id=item['product'])
            if product.stock_count < item['quantity']:
                raise ValidationError(
                f"Not enough stock for {product.name}. Available: {product.stock_count}"
                )
        for item in order_items_data:
            order_items = item.copy()
            print(f"productID: {item['product']}")
            product = Product.objects.get(id=item['product'])
            product.stock_count = product.stock_count - item['quantity']
            update_product(request, product.id, {'stock_count': product.stock_count})
            order_items['product'] = product
            OrderItems.objects.create(order=order, **order_items)
    response = OrderSerializer(order)
    try:
        delete_order_chunks(order_id)
        message = "Product chunks deleted successfully"
        insert_order_and_items_chunks(response.data)  # Pass the model instance directly
    except Exception as e:
        print(f"Error updating product chunks: {e}")
        message = "Error deleting product chunks"
    return order    
    


# ------------------------------------------------------
# 💰 DISCOUNT MESSAGE SERVICE
# ------------------------------------------------------

def build_discount_messages(request, amount_min=1000, k=5, with_text=False):
    """
    Build discount or recommendation messages for top customers.
    """
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role build discount messages: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager", "Customer_Service"}
    if role not in allowed_roles:
        raise PermissionDenied()  
    t0 = now() - timedelta(days=7)
    spend = (
        Order.objects
        .filter(created_at__gte=t0, status__in=["Order_Finished", "Order_Delivered"])
        .values("customer_id")
        .annotate(total_week=Sum("grand_price"))
        .filter(total_week__gt=amount_min)
        .order_by("-total_week")
    )
    
    results = []
    for row in spend:
        print(f"spendOrders: {row}")
        try:
            customer = Customer.objects.get(id=row["customer_id"])
        except Customer.DoesNotExist:
            continue

        recs, context = recommend_products_for_customer(customer, k=k)
        print(f"recommendations: {recs}")
        print(f"context: {context}")
        msg = None
        if with_text:
            msg = build_discount_message_for_customer(
                customer, recs, context,
                policy={
                    "discount_pct": 15,
                    "deadline": "3 days from now",
                    "exclusions": "excludes already discounted items"
                }
            )
        print(f"result: {results}")    
        results.append({
            "customer_id": customer.id,
            "customer_name": f"{customer.first_name} {customer.last_name}",
            "total_week": row["total_week"],
            "suggestions": recs,
            "message": msg
        })

    return results


# ------------------------------------------------------
# 💬 ORDER EXPLAIN SERVICE
# ------------------------------------------------------

def get_order_explanation(request, order_id):
    """
    Return AI-generated explain message for a specific order.
    """
    employee = get_employee(request, request.user.id)
    role = employee.role
    print(f"request User Role: {role}")
    allowed_roles = {"Top_Manager", "Customer_Service_Manager", "Customer_Service"}
    if role not in allowed_roles:
        raise PermissionDenied()
    try:
        order = Order.objects.select_related("customer").get(id=order_id)
    except Order.DoesNotExist:
        return None, {"error": "order not found"}

    items = list(
        OrderItems.objects.filter(order=order)
        .values("product__title", "quantity", "product__price")
    )

    context_rows = [
        f"- {r['product__title']} x{r['quantity']} @ {r['product__price']}"
        for r in items
    ]

    data = build_order_explain_prompt(order, context_rows)

    result = {
        "order_id": order.id,
        "message": data["message"],
        "evidence": [
            {"id": c["id"], "source": c["source"], "distance": c["distance"]}
            for c in data["retrieved"]
        ]
    }

    return result, None
