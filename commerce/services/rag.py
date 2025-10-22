# api/services/rag.py
import os
from typing import List, Dict, Tuple, Optional
from django.db import connection
from orders.models import OrderItems, Order
from products.models import Product
from customers.models import Customer


# استخدم دالة get_embedding اللي سبق وكتبناها
from commerce.services.embeddings import get_embedding, to_sql_vector
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --------- LLM stub (وصّله بمزوّدك) ----------
def llm_chat(system: str, user: str) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print(f"systemMessage: {system}")
    print(f"userMessage: {user}")
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    max_completion_tokens = 500,
    messages=[
        {"role": "system", "content": system,
            "role": "user", "content": user
            }
        ]
    )
    print(f"ChatGPTResponse: {response.choices[0].message.content}")
    return response.choices[0].message.content

# --------- Vector search over admin_chunk ----------
def _search_admin_chunks(query: str, k: int = 12,
                         entity_type: str | None = None) -> List[Dict]:
    q_emb = get_embedding(query)
    emb_lit = to_sql_vector(q_emb)
    where = "WHERE 1=1"
    if entity_type:
        where += " AND entity_type = %s"
        params = [entity_type]
    else:
        params = []
    sql = f"""
    WITH q AS (SELECT {emb_lit}::vector AS emb)
    SELECT id, entity_type, entity_id, source, text,
           (embedding <-> (SELECT emb FROM q)) AS distance
    FROM admin_chunk
    {where}
    ORDER BY embedding <-> (SELECT emb FROM q)
    LIMIT {k};
    """
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {"id": r[0], "entity_type": r[1], "entity_id": r[2],
         "source": r[3], "text": r[4], "distance": float(r[5])}
        for r in rows
    ]
    
def search_admin_chunks(query: str, k: int = 12,
                        entity_type: Optional[str] = None,
                        entity_id: Optional[int] = None,
                        filters_sql: Optional[List[Tuple[str, Optional[str]]]] = None) -> List[Dict]:
    """
    filters_sql: list of (key,value) تُستخدم فقط لإرشاد LLM عبر إضافة سطور tag في النص المصدر،
    أو تجاهلها إن جدولك admin_chunk مش مخزنها كسطور. تقدر تشيلها لو مش محتاجها.
    """
    emb = get_embedding(query)
    emb_lit = to_sql_vector(emb)
    where = []
    params: List[object] = []
    if entity_type:
        where.append("entity_type = %s"); params.append(entity_type)
    if entity_id:
        where.append("entity_id = %s"); params.append(entity_id)

    sql = f"""
    WITH q AS (SELECT {emb_lit}::vector AS emb)
    SELECT id, entity_type, entity_id, source, text,
           (embedding <-> (SELECT emb FROM q)) AS distance
    FROM admin_chunk
    {"WHERE " + " AND ".join(where) if where else ""}
    ORDER BY embedding <-> (SELECT emb FROM q)
    LIMIT {k};
    """
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        {"id": r[0], "entity_type": r[1], "entity_id": r[2],
         "source": r[3], "text": r[4], "distance": float(r[5])}
        for r in rows
    ]    

# --------- Customer history & preferences ----------
def _customer_recent_titles(customer: Customer, n: int = 5) -> List[str]:
    items = (OrderItems.objects
             .filter(order__customer=customer)
             .order_by("-order__created_at")[:n]
             .select_related("product"))
    return [it.product.title for it in items if it.product_id]

# --------- Recommend products (semantic + business filters) ----------
def recommend_products_for_customer(customer: Customer, k: int = 6) -> Tuple[List[Dict], str]:
    hist_titles = _customer_recent_titles(customer, n=6)
    if not hist_titles:
        # fallback: popular products last week
        t_items = (OrderItems.objects
                   .filter(order__status__in=["completed","delivered"])
                   .values("product_id")
                   .annotate(units_sum=Sum("quantity"))
                   .order_by("-units_sum")[:k])
        ids = [x["product_id"] for x in t_items]
        qs = Product.objects.filter(id__in=ids).values("id","title","price","stock_count","rating")
        recs = list(qs)
        context = "No purchase history; using weekly popular items."
        return recs, context

    # vector search using history titles as query
    query = "similar products to: " + ", ".join(hist_titles)
    chunks = _search_admin_chunks(query, k=24, entity_type="product")
    # business filters: available & distinct top-k by product id
    product_ids = []
    dedup = []
    for ch in chunks:
        pid = ch["entity_id"]
        if pid not in product_ids:
            product_ids.append(pid)
        if len(product_ids) >= k * 2:
            break

    products = (Product.objects
                .filter(id__in=product_ids, stock_count__gt=0)
                .values("id","title","price","stock_count","rating")
                .order_by("-rating"))
    recs = list(products[:k])
    context = "\n".join([f"[{i+1}] {r['title']} | price={r['price']} | rating={r['rating']}"
                         for i, r in enumerate(recs)])
    return recs, context

# --------- Build messages (context-only prompts) ----------
def build_recommendation_message(customer: Customer, recs: List[Dict], context: str) -> str:
    system = (
        "أنت مساعد تسويق لمتجر إلكتروني. اكتب رسالة توصيات قصيرة بالعربية "
        "باستخدام العناصر المقترحة فقط. لا تخترع معلومات. اذكر سبب موجز لكل منتج."
    )
    items_txt = "\n".join([f"- {r['title']} — السعر: {r['price']}" for r in recs])
    user = f"العميل: {customer.first_name} {customer.last_name}\n\nالعناصر المقترحة:\n{items_txt}\n\nContext:\n{context}\n"
    return llm_chat(system=system, user=user)

def build_discount_message_for_customer(customer: Customer, recs: List[Dict], context: str, policy: Dict) -> str:
    system = (
        "أنت مساعد تسويق. اكتب رسالة خصم قصيرة بالعربية. استخدم فقط العناصر وسياسة الخصم المرفقة. "
        "لا تذكر أي بيانات شخصية حساسة. كن ودودًا ومباشرًا."
    )
    items_txt = "\n".join([f"- {r['title']} — السعر: {r['price']}" for r in recs])
    policy_txt = f"خصم {policy.get('discount_pct',15)}% حتى {policy.get('deadline','قريبًا')}. استثناءات: {policy.get('exclusions','لا يوجد')}."
    user = (f"العميل: {customer.first_name} {customer.last_name}\n"
            f"سياسة الخصم: {policy_txt}\n\n"
            f"العناصر المقترحة:\n{items_txt}\n\n"
            f"Context:\n{context}\n\n"
            "اكتب الرسالة النهائية.")
    return llm_chat(system=system, user=user)


def build_order_explain_prompt(o: Order, item_rows: List[str]) -> Dict[str, str]:
    ctx = [
        f"Order Snapshot: id={o.id}, status={o.status}, payment={o.payment_status}, grand={o.grand_price}, address={(o.address or '')[:64]}..."
    ]
    ctx += [f"Item {i+1}: {r}" for i, r in enumerate(item_rows)]
    # Retrieve any admin chunks for this order (optional—if كنت بتخزّن snapshots)
    chunks = search_admin_chunks(
            f"explain order status and shipping/payment details for order {o.id}",
            k=8, entity_type="order", entity_id=o.id
        )
    for i, c in enumerate(chunks, 1):
        ctx.append(f"[{i}] {c['source']} :: {c['text'][:300]}")
    system = (
        "أنت موظف دعم. اكتب رسالة عربية بسيطة للعميل تشرح حالة الطلب والخطوة التالية، "
        "وذكّر بوسيلة الدفع والشحن باختصار. استخدم فقط السياق، وإن لم تكفِ البيانات قل: لا أعلم."
    )
    user = "Context:\n" + "\n".join(ctx) + "\n\nأخرج: رسالة قصيرة + نقاط واضحة + المراجع [أرقام المقاطع إن وجدت]."
    return {"message": llm_chat(system=system,user=user), "retrieved": chunks}


def build_restock_prompt(category_name: str, filtered_rows: List[Dict], ranked_chunks: List[Dict]) -> Dict[str, str]:
    tbl = "\n".join(
        [f"- {r['id']} | {r['title']} | stock={r['stock_count']} | rating={r.get('rating','')} | price={r['price']}"
         for r in filtered_rows[:50]]
    )
    ev = "\n".join([f"[{i+1}] pid={c['entity_id']} :: {c['source']}" for i, c in enumerate(ranked_chunks)])
    system = (
        "أنت مستشار مخزون. اقترح قائمة قصيرة لإعادة الطلب (Restock) لمنتجات منخفضة المخزون وعالية التأثير "
        "ضمن الكاتيجري المحدد. استخدم فقط البيانات التالية."
    )
    user = f"Category: {category_name}\nFiltered (low stock):\n{tbl}\n\nEvidence:\n{ev}\n\nأخرج: Top 10 مع سبب موجز لكل عنصر + أولوية."
    return llm_chat(system=system,user=user)

# --------- Restock helper (rank already filtered low-stock list) ----------
def find_high_impact_restock(rows: List[Dict]) -> List[Dict]:
    """
    rows: [{'id','title','category__name','stock_count','price','rating'}, ...]
    يرجّع Top-10 مرتّبة heuristically (rating desc, stock asc)
    """
    rows = sorted(rows, key=lambda r: (-float(r.get("rating") or 0), float(r.get("stock_count") or 0)))
    return rows[:10]
