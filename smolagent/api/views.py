from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import os
import time
from dotenv import load_dotenv
from asgiref.sync import sync_to_async

from .serializers import ApiLogSerializer
from smolagent.models import ApiLog
from smolagent.ai_agent_service import run_smolagent
from products.api.services import (list_products, get_product, create_product, update_product, delete_product,
                                   get_restock_advice, get_products_by_name_and_brand)
from products.api.serializers import ProductReadSerializer, ProductSerializer
from categories.api.services import get_category, list_categories
from categories.api.serializers import CategorySerializer
from orders.api.serializers import OrderCreateSerializer, OrderItemsSerializer
from orders.api.services import get_order_by_id_with_products, create_order_and_recommend, build_discount_messages, get_order_explanation, update_order
from customers.api.services import get_customer, list_customers, search_customers
from customers.api.serializers import CustomerSerilazer


ALLOWED_FUNCTIONS = {
    "get_all_products": list_products,
    "get_product_by_product_id": get_product,
    "get_product_by_product_name_or_brand": get_products_by_name_and_brand,
    "add_new_product": create_product,
    "update_product": update_product,
    "delete_product": delete_product,
    "get_advice_for_restock_products": get_restock_advice,
    "get_category_by_id": get_category,
    "list_categories": list_categories,
    "get_order_by_order_number": get_order_by_id_with_products,
    "create_order": create_order_and_recommend, 
    "update_order_by_order_number": update_order,
    "get_order_explanation": get_order_explanation,
    "build_discount_message": build_discount_messages,
    "get_customer_by_id": get_customer,
    "get_all_customers": list_customers,
    "search_customers": search_customers,
}

load_dotenv()


@api_view(["POST"])
def run_function_view(request):
    start_time = time.time()
    endpoint = request.path
    method = request.method
    token = request.headers.get('X-Internal-Token')
    if token != os.getenv("INTERNAL_API_TOKEN"):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    body = json.loads(request.body)
    fn_name = body.get("function")
    params = body.get("params", {})
    context = body.get("context", {})

    if fn_name not in ALLOWED_FUNCTIONS:
        return JsonResponse({"error": "Function not allowed"}, status=403)

    #employee_id = context.get("employee_id")
    print(f"function name: {fn_name}")
    if ALLOWED_FUNCTIONS[fn_name] == list_products:
        result = ProductReadSerializer(list_products(), many=True)
        response = JsonResponse({"result": result.data})
    elif ALLOWED_FUNCTIONS[fn_name] == get_product:
        result = ProductReadSerializer(get_product(params['product_id'])) 
        response = JsonResponse({"result": result.data})  
    elif ALLOWED_FUNCTIONS[fn_name] == get_products_by_name_and_brand:
        print(f"getProductsByName and category: {params}")
        brand = None
        if 'brand' in params:
            brand = params['brand']
        print(f"getProductsByName and category: {params['name']}")
        result = ProductReadSerializer(get_products_by_name_and_brand(request, params['name'], brand), many=True)
        response = JsonResponse({"result": result.data})     
    elif ALLOWED_FUNCTIONS[fn_name] == create_product:
        data = params.copy()
        data["created_by"] = request.user.id
        serializer = ProductSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        result = ProductReadSerializer(create_product(request, serializer.validated_data))
        response = JsonResponse({"result": result.data})
    elif ALLOWED_FUNCTIONS[fn_name] == update_product:
        result = ProductReadSerializer(update_product(request, params['product_id'], params))  
        response = JsonResponse({"result": result.data})   
    elif ALLOWED_FUNCTIONS[fn_name] == delete_product:
        result = delete_product(request, params['product_id'])
        response = JsonResponse({"result": result})
    elif ALLOWED_FUNCTIONS[fn_name] == get_restock_advice:
        result = get_restock_advice(request, params['category'], params['threshold'], params['max_products'])   
        print(f"get restock advice result: {result}")
        response = JsonResponse({"result": result})
    elif ALLOWED_FUNCTIONS[fn_name] == list_categories:
        result = CategorySerializer(list_categories(), many=True)
        print(f"list categories result: {result.data}")
        response = JsonResponse({"result": result.data})
    elif ALLOWED_FUNCTIONS[fn_name] == get_category:
        result = CategorySerializer(get_category(params['category_id'])) 
        print(f"categoryById result: {result.data}")   
        response = JsonResponse({"result": result.data}) 
    elif ALLOWED_FUNCTIONS[fn_name] == get_order_by_id_with_products:
        response = JsonResponse({"result": get_order_by_id_with_products(request, params['order_id'])})   
    elif ALLOWED_FUNCTIONS[fn_name] == create_order_and_recommend:
        data = params.copy()
        data["created_by"] = request.user.id
        print(f"create order params: {data}")
        serializer = OrderCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        result = create_order_and_recommend(request, serializer)
        response = JsonResponse({"result": result})
    elif ALLOWED_FUNCTIONS[fn_name] == update_order:
        result = OrderCreateSerializer(update_order(request, params['order_id'], params))  
        response = JsonResponse({"result": result.data})      
    elif ALLOWED_FUNCTIONS[fn_name] == get_order_explanation:
        response = JsonResponse({"result": get_order_explanation(request, params['order_id'])})   
    elif ALLOWED_FUNCTIONS[fn_name] == build_discount_messages:
        response = JsonResponse({"result": build_discount_messages(request, params['min_num_products'], params['num_products_to_recommend'])})   
    elif ALLOWED_FUNCTIONS[fn_name] == get_customer:
        result = CustomerSerilazer(get_customer(request, params['customer_id']))   
        response = JsonResponse({"result": result.data})
    elif ALLOWED_FUNCTIONS[fn_name] == list_customers:
        result = CustomerSerilazer(list_customers(request))   
        response = JsonResponse({"result": result.data})
    elif ALLOWED_FUNCTIONS[fn_name] == search_customers:
        phone = None
        if 'phone' in params:
            phone = params['phone']
        address = None
        if 'address' in params:
            address = params['address']
        result = CustomerSerilazer(search_customers(request, params['name'], phone, address), many=True)   
        response = JsonResponse({"result": result.data})         
    else:
        result = None    
    end_time = time.time()
    response_time_ms = round((end_time - start_time) * 1000, 2)   
    response_body = json.loads(response.content)
    status_code = response.status_code
    ApiLog.objects.create(
        endpoint=endpoint,
        method=method,
        request_data=body,
        response_data=response_body,
        status_code=status_code,
        response_time=response_time_ms,
    )                
    return response


@api_view(['GET'])
def run_chat_view(request):
    start_time = time.time()
    request_data = request.data
    endpoint = request.path
    method = request.method
    query = request.GET.get('query')
    same_chat = request.GET.get('same_chat', 'false').lower() == 'true'
    print(f"request same_chat: {same_chat}")
    if not query:
        return JsonResponse({'error': 'Query parameter is required'}, status=400)
    try:
        result = run_smolagent(request, query, same_chat)
        response = JsonResponse({"result": result})
        end_time = time.time()
        response_time_ms = round((end_time - start_time) * 1000, 2)   
        response_body = json.loads(response.content)
        status_code = response.status_code
        ApiLog.objects.create(
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            response_data=response_body,
            status_code=status_code,
            response_time=response_time_ms,
        )
        return response
    except Exception as e:
        response = JsonResponse({"error": str(e)}, status=500)
        end_time = time.time()
        response_time_ms = round((end_time - start_time) * 1000, 2)   
        response_body = json.loads(response.content)
        status_code = response.status_code
        ApiLog.objects.create(
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            response_data=response_body,
            status_code=status_code,
            response_time=response_time_ms,
        )
        return response
