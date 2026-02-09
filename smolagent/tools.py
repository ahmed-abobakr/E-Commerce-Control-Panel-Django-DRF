import requests
from dotenv import load_dotenv
import os


from smolagents import tool
from categories.models import Category

load_dotenv()

INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN")
def run_backend_tool(func_name, params, context):
    """Call the internal backend function runner and return a normalized response.

    Success path (HTTP 2xx and a JSON payload containing a `result` field):
        - returns the value of `result` (keeps backward-compatibility with existing tools)

    Error path (network/timeout/invalid JSON/HTTP non-2xx/missing `result`):
        - returns a dict with a stable schema so the agent/LLM can understand what happened:
            {
              "ok": False,
              "function": str,
              "status_code": int | None,
              "error": str,
              "details": any,
              "hint": str
            }
    """
    print("run backend tool")
    url = "http://127.0.0.1:8000/ai_agent/api/internal/run_function/"
    headers = {
        "X-Internal-Token": INTERNAL_API_TOKEN,
        # avoid KeyError if context doesn't include agent_token
        "Authorization": f"{(context or {}).get('agent_token', '')}",
    }
    payload = {"function": func_name, "params": params, "context": context}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as e:
        return {
            "ok": False,
            "function": func_name,
            "status_code": None,
            "error": f"Request failed: {type(e).__name__}: {str(e)}",
            "details": {"url": url, "payload": payload},
            "hint": "Check backend server is reachable and INTERNAL_API_TOKEN/agent_token are valid. Then retry the same tool call.",
        }

    status_code = getattr(resp, "status_code", None)

    try:
        data = resp.json()
    except ValueError:
        text_preview = (resp.text or "")[:2000]
        return {
            "ok": False,
            "function": func_name,
            "status_code": status_code,
            "error": "Backend returned a non-JSON response.",
            "details": {"text_preview": text_preview},
            "hint": "Inspect backend logs for the failure reason (500/traceback). Fix the backend response to return JSON consistently.",
        }

    print(f"internal function response: {data}")

    is_http_ok = status_code is not None and 200 <= int(status_code) < 300
    has_result = isinstance(data, dict) and ("result" in data)

    if is_http_ok and has_result:
        return data.get("result")

    # extract best error message
    error_msg = None
    if isinstance(data, dict):
        for k in ("error", "detail", "message", "errors"):
            if k in data and data[k]:
                error_msg = data[k]
                break

    if not error_msg:
        error_msg = f"Backend call failed (HTTP {status_code})."

    return {
        "ok": False,
        "function": func_name,
        "status_code": status_code,
        "error": error_msg if isinstance(error_msg, str) else str(error_msg),
        "details": data,
        "hint": "Review `details`, fix params/context, and retry. If 401/403 check tokens; if 400 validate required params types/values.",
    }

@tool
def get_all_products(request: requests.Request) -> list:
    """
    Get list of All Products 
    Args:
        request: Django Request Object   
    Returns:
        list of products each product is dict contains id, title, price, description, stock_count, category_detail which contins id, name and parent_id of categorty
    """
    return run_backend_tool("get_all_products", {}, {'agent_token': request.headers.get('Authorization')})



@tool
def get_product_by_product_id(request: requests.Request, product_id: str) -> dict:
    """
    Get Product by Product ID   
     
    Args:
        request: Django Request Object
        product_id: Product ID

    Returns:
        dict: Product Details contains id, title, price, description, stock_count, category_detail which contins id, name and parent_id of categorty
    """
    return run_backend_tool("get_product_by_product_id", {"product_id": product_id}, {'agent_token': request.headers.get('Authorization')})


@tool
def create_product(request: requests.Request, title: str, price: float, description: str, stock_count: int, category_id: int, brand: str, rating: int) -> dict:
    """
    Create a New Product
    Args:
        request: Django Request Object
        title: Product Title
        price: Product Price
        description: Product Description
        stock_count: Product Stock Count
        category_id: Product Category ID
        brand: Product Brand
        rating: Product Rating

    Returns:
        dict: Product Details contains id, title, price, description, stock_count, category_detail which contins id, name and parent_id of categorty
    """
    return run_backend_tool("add_new_product", {"title": title, "price": price, "description": description, "stock_count": stock_count, "category_id": category_id, "brand": brand, "rating": rating},
                            {'agent_token': request.headers.get('Authorization')})


@tool
def update_product(request: requests.Request, product_id: str, title: str, price: float, description: str, stock_count: int, category_id: int, brand: str, rating: int) -> dict:
    """
    Update Product Details    
    Args:
        request: Django Request Object
        product_id: Product ID
        title: Product Title
        price: Product Price
        description: Product Description
        stock_count: Product Stock Count
        category_id: Product Category ID
        brand: Product Brand
        rating: Product Rating

    Returns:
        dict: Product Details contains id, title, price, description, stock_count, category_detail which contins id, name and parent_id of categorty
    """
    return run_backend_tool("update_product", {"product_id": product_id, "title": title, "price": price, "description": description, "stock_count": stock_count, "category_id": category_id, "brand": brand,"rating": rating},
                            {'agent_token': request.headers.get('Authorization')})

@tool
def delete_product(request: requests.Request, product_id: str) -> bool:
    """
    Delete Product by Product ID    
    Args:
        request: Django Request Object
        product_id: Product ID

    Returns:
        True for found and Deleted product
        False for not found product
    """
    return run_backend_tool("delete_product", {"product_id": product_id}, {'agent_token': request.headers.get('Authorization')})


@tool
def get_advice_for_restock_products(request: requests.Request, category: Category, threshold: int, max_products: int) -> dict:
    """
    Get Restock Advice for Products in Category    
    Args:
        request: Django Request Object
        category: Category Object to be  like {"category": {"id": 1, "name": "Electronics", "parent_id": null}}
        threshold: Threshold Stock Count
        max_products: Max Products to Recommend

    Returns:
        json contains count of products to restock, filtered which list of products need to restock, top_ranked list of top product Ids and advice which is string for products should be asked to restock
    """
    return run_backend_tool("get_advice_for_restock_products", {"category": {"id": category['id'], "name": category['name'], "parent_id": category['parent_id']}, "threshold": threshold, "max_products": max_products}, 
                            {'agent_token': request.headers.get('Authorization')})
    
@tool
def get_all_categories(request: requests.Request) -> list:
    """
    Get list of All Categories
    Args:
        request: Django Request Object    
    Returns:
        list of categories each category is dict contains id, name, parent_category_id
    """
    response = run_backend_tool("list_categories", {}, {'agent_token': request.headers.get('Authorization')})
    print(f"get_all_categories response: {response}")
    return response


@tool
def get_category_by_id(request: requests.Request, category_id: str) -> dict:
    """
    Get Category by Category ID    
    Args:
        request: Django Request Object
        category_id: Category ID

    Returns:
        dict: Category Details contains id, name, parent_category_id
    """
    return run_backend_tool("get_category_by_id", {"category_id": category_id}, {'agent_token': request.headers.get('Authorization')})


@tool
def get_order_by_id(request: requests.Request, order_id: str) -> dict:
    """
    Get Order details with products by Order ID
    Args:
        request: Django Request Object
        order_id: Order ID
    Returns:
        dict: Order details with products
    """
    return run_backend_tool("get_order_explanation", {"order_id": order_id}, {'agent_token': request.headers.get('Authorization')})

@tool
def create_order(
    request: requests.Request,
    sub_total: float,
    tax_total: float,
    shipping_price: float,
    grand_price: float,
    customer: str,
    address: str,
    payment_status: str,
    product_ids: list[str],
    quantities: list[str],
    discount_total: float = None,
    status: str = "Order_Finished",
) -> dict:
    """
    Create a new order with order items (robust, self-correcting inputs).

    This tool is intentionally forgiving: it accepts customer/product identifiers as IDs (int)
    or as human-readable names (str). It also tolerates multiple shapes for product inputs.

    Args:
        request: Django Request Object
        sub_total: Order subtotal
        tax_total: Tax amount
        shipping_price: Shipping cost
        grand_price: Total price
        customer: Customer ID (int) OR customer name (str)
        address: Shipping address
        payment_status: Payment method (Cash, Visa, Smart_Wallet)
        product_ids: One of:
            - list[int] product IDs
            - list[str] product titles (will be resolved)
            - list[dict] items like {"product": <id or title>, "quantity": <int>}
        quantities: Optional list[int] quantities matching product_ids, OR a single int applied to all.
        discount_total: Optional discount amount
        status: Order status (default: Order_Finished)(Order Finished, Preparing, Order Ready, Oreder Delivering, Order Delivered)

    Returns:
        On success: dict order details (backend `result`)
        On failure: dict with stable error fields: ok/function/status_code/error/details/hint
    """
    ctx = {"agent_token": request.headers.get("Authorization")}

    def _fail(msg: str, details=None, hint: str = ""):
        return {
            "ok": False,
            "function": "create_order",
            "status_code": None,
            "error": msg,
            "details": details,
            "hint": hint or "Fix the arguments, then retry create_order.",
        }

    # -------------------------
    # Normalize customer
    # -------------------------
    customer_id = None
    if isinstance(customer, int):
        customer_id = customer
    elif isinstance(customer, str):
        name = customer.strip()
        if not name:
            return _fail("Customer name is empty.", {"customer": customer})
        matches = run_backend_tool("search_customers", {"name": name}, ctx)
        # If backend returned an error dict, pass it through (adds clarity)
        if isinstance(matches, dict) and matches.get("ok") is False:
            matches.setdefault("hint", "search_customers failed; check tokens and backend.")
            return matches
        if not matches:
            return _fail(
                f"No customer found matching name '{name}'.",
                {"query": name},
                "Call get_all_customers or search_customers with a broader name, then use the returned customer id.",
            )
        if isinstance(matches, list) and len(matches) > 1:
            # Provide small preview of candidates
            preview = []
            for c in matches[:5]:
                if isinstance(c, dict):
                    preview.append({"id": c.get("id"), "name": c.get("name") or c.get("full_name")})
                else:
                    preview.append(str(c))
            return _fail(
                f"Multiple customers match '{name}'. Please choose a specific customer id.",
                {"candidates": preview},
                "Retry create_order with customer=<id> from candidates.",
            )
        # single match
        if isinstance(matches, list) and matches and isinstance(matches[0], dict):
            customer_id = matches[0].get("id")
        elif isinstance(matches, dict):
            customer_id = matches.get("id")
        if not customer_id:
            return _fail(
                "Could not resolve customer id from search results.",
                {"matches": matches},
                "Call get_all_customers and pick an exact customer id.",
            )
    else:
        return _fail(
            "Invalid type for customer. Use int customer id or str customer name.",
            {"customer": customer, "type": str(type(customer))},
        )

    # -------------------------
    # Normalize product inputs
    # -------------------------
    # Allow product_ids to be: list[int] | list[str] | list[dict]
    # If list[dict], prefer that and ignore `quantities`.
    normalized_items = []

    if product_ids is None:
        return _fail("product_ids is required and cannot be null.", {"product_ids": product_ids})

    # If caller passed a single item, wrap it
    if not isinstance(product_ids, list):
        product_ids = [product_ids]

    # Case 1: list of dict items with product + quantity
    if product_ids and all(isinstance(x, dict) for x in product_ids):
        for item in product_ids:
            prod = item.get("product") or item.get("product_id") or item.get("title")
            qty = item.get("quantity")
            if qty is None:
                return _fail("Missing quantity for an order item.", {"item": item})
            try:
                qty_int = int(qty)
            except Exception:
                return _fail("Quantity must be an integer.", {"quantity": qty, "item": item})
            if qty_int <= 0:
                return _fail("Quantity must be >= 1.", {"quantity": qty_int, "item": item})

            normalized_items.append({"product": prod, "quantity": qty_int})

    else:
        # Case 2: product_ids list + separate quantities
        if quantities is None:
            return _fail(
                "quantities is required when product_ids is not a list of dict items.",
                {"product_ids": product_ids, "quantities": quantities},
                "Provide quantities as list[int] aligned with product_ids, or pass product_ids as list of {product, quantity}.",
            )

        # quantities can be single int or list
        if isinstance(quantities, int):
            quantities = [quantities] * len(product_ids)
        if not isinstance(quantities, list):
            return _fail(
                "Invalid quantities type. Provide list[int] or a single int.",
                {"quantities": quantities, "type": str(type(quantities))},
            )
        if len(product_ids) != len(quantities):
            return _fail(
                "product_ids and quantities must have the same length.",
                {"product_ids_len": len(product_ids), "quantities_len": len(quantities)},
                "Make sure each product has a matching quantity.",
            )

        for prod, qty in zip(product_ids, quantities):
            try:
                qty_int = int(qty)
            except Exception:
                return _fail("Quantity must be an integer.", {"quantity": qty, "product": prod})
            if qty_int <= 0:
                return _fail("Quantity must be >= 1.", {"quantity": qty_int, "product": prod})
            normalized_items.append({"product": prod, "quantity": qty_int})

    # -------------------------
    # Resolve product titles -> IDs (if needed)
    # -------------------------
    # If any product value is a string, try to map by title from get_all_products.
    needs_resolution = any(isinstance(it.get("product"), str) for it in normalized_items)

    products_cache = None
    if needs_resolution:
        products_cache = run_backend_tool("get_all_products", {}, ctx)
        if isinstance(products_cache, dict) and products_cache.get("ok") is False:
            products_cache.setdefault("hint", "get_all_products failed; check tokens and backend.")
            return products_cache
        if not isinstance(products_cache, list) or not products_cache:
            return _fail(
                "Could not load products to resolve titles.",
                {"products": products_cache},
                "Ensure backend returns a list of products. Then retry.",
            )

        def _resolve_product_id(title: str):
            t = title.strip().lower()
            # exact match first
            for p in products_cache:
                if isinstance(p, dict) and str(p.get("title", "")).strip().lower() == t:
                    return p.get("id")
            # contains match fallback
            for p in products_cache:
                if isinstance(p, dict) and t and t in str(p.get("title", "")).strip().lower():
                    return p.get("id")
            return None

        for it in normalized_items:
            prod = it.get("product")
            if isinstance(prod, str):
                pid = _resolve_product_id(prod)
                if not pid:
                    # show a small suggestion list
                    suggestions = []
                    for p in products_cache[:10]:
                        if isinstance(p, dict):
                            suggestions.append({"id": p.get("id"), "title": p.get("title")})
                    return _fail(
                        f"Could not resolve product title '{prod}' to a product id.",
                        {"suggestions": suggestions},
                        "Retry create_order using product_ids as IDs, or use a product title that exactly matches an existing product.",
                    )
                it["product"] = pid

    # Final items to backend
    order_items = [{"product": it["product"], "quantity": it["quantity"]} for it in normalized_items]

    # Optional: if grand_price seems missing/zero, compute a safe fallback
    try:
        if grand_price is None:
            grand_price = (float(sub_total or 0) + float(tax_total or 0) + float(shipping_price or 0)) - float(discount_total or 0)
    except Exception:
        # leave as-is if computation fails
        pass

    params = {
        "sub_total": sub_total,
        "tax_total": tax_total,
        "shipping_price": shipping_price,
        "grand_price": grand_price,
        "customer": customer_id,
        "address": address,
        "payment_status": payment_status,
        "order_items": order_items,
        "discount_total": discount_total,
        "status": status,
    }

    result = run_backend_tool("create_order", params, ctx)

    # If backend returned normalized error dict, enrich hint for self-correction
    if isinstance(result, dict) and result.get("ok") is False:
        result.setdefault(
            "hint",
            "Backend rejected the request. Re-check required fields and value types. If it's a 400, validate payment_status/status values and ensure product/customer IDs exist.",
        )
    return result

@tool
def get_order_explanation(request: requests.Request, order_id: str) -> dict:
    """
    Get AI explanation for an order
    Args:
        request: Django Request Object
        order_id: Order ID
    Returns:
        dict: Explanation and evidence
    """
    return run_backend_tool("get_order_explanation", {"order_id": order_id}, {'agent_token': request.headers.get('Authorization')})

@tool
def build_discount_message(request: requests.Request, customer_id: int) -> dict:
    """
    Build discount message for a customer
    Args:
        request: Django Request Object
        customer_id: Customer ID
    Returns:
        dict: Discount recommendations
    """
    return run_backend_tool("build_discount_message", {"customer_id": customer_id}, {'agent_token': request.headers.get('Authorization')})

@tool
def get_all_customers(request: requests.Request) -> list:
    """
    Get list of all customers
    Args:
        request: Django Request Object
    Returns:
        list of customer details
    """
    return run_backend_tool("get_all_customers", {}, {'agent_token': request.headers.get('Authorization')})

@tool
def get_customer_by_id(request: requests.Request, customer_id: str) -> dict:
    """
    Get customer details by ID
    Args:
        request: Django Request Object
        customer_id: Customer ID
    Returns:
        dict: Customer details
    """
    return run_backend_tool("get_customer_by_id", {"customer_id": customer_id}, {'agent_token': request.headers.get('Authorization')})

@tool
def search_customers(request: requests.Request, name: str, phone: str = None, address: str = None) -> list:
    """
    Search customers by name and optionally phone/address
    Args:
        request: Django Request Object
        name: Search query for customer name
        phone: Optional phone number filter
        address: Optional address filter
    Returns:
        list of matching customers
    """
    params = {"name": name}
    if phone:
        params["phone"] = phone
    if address:
        params["address"] = address
    return run_backend_tool("search_customers", params, {'agent_token': request.headers.get('Authorization')})

@tool
def get_product_by_product_name_or_brand(request: requests.Request, name: str, brand: str = None) -> list:
    """
    Get products by name and optionally brand
    Args:
        request: Django Request Object
        name: Product name search query
        brand: Optional brand filter
    Returns:
        list of matching products
    """
    params = {"name": name}
    if brand:
        params["brand"] = brand
    return run_backend_tool("get_product_by_product_name_or_brand", params, {'agent_token': request.headers.get('Authorization')})