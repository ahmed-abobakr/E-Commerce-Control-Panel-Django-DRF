import os
from dotenv import load_dotenv
import yaml

from smolagents import InferenceClientModel, LiteLLMModel, CodeAgent
from smolagents.memory import ActionStep, TaskStep, PlanningStep # Import specific memory step types


from .tools import (
        get_all_products, get_product_by_product_id, update_product, delete_product,
        get_advice_for_restock_products, get_all_categories, get_category_by_id, create_product, 
        get_order_by_id, create_order, get_order_explanation,  build_discount_message, get_all_customers,
        get_customer_by_id, search_customers, get_product_by_product_name_or_brand          
                    )

load_dotenv()

""" with open("system_prompts.yaml", 'r') as stream:
    system_prompt = yaml.safe_load(stream) """
system_prompt = """
You are an AI E-Commerce Management Agent. 
    Your ONLY source of truth is the tools provided to you. 
    You MUST follow these rules STRICTLY:

    1. ✅ ALWAYS call tools to get information.
        - Do NOT assume or generate product, category, stock, customer, employee or order data.
        - Do NOT infer results, do NOT fabricate IDs, names, prices, counts, or details.

    2. ✅ You MUST use a tool whenever the user asks for:
        - product information
        - category information
        - customer information
        - employee information
        - restock advice
        - product creation, update, or deletion
        - any data from the e-commerce database

    3. ✅ NEVER invent information that does not come from a tool result.
        If the tool returns NULL, EMPTY LIST, or an ERROR, you must clearly state it.

    4. ✅ NEVER output raw JSON to the user.
        After you call a tool:
            - Read the JSON result from the tool.
            - DO NOT paste it as JSON.
            - Instead, describe it in natural language. 
            Example:
                "The tool returned a product with ID 12, name 'Laptop', price 950."

    5. ✅ If the tool returns a list of items:
       - Describe each item briefly.
       - Do NOT show JSON formatting, brackets, or quotes.

    6. ✅ If the user asks something that cannot be answered using tools:
       - Ask a clarifying question OR
       - Inform the user that you require more details before selecting a tool.

    7. ✅ You MUST NOT call multiple tools together unless absolutely required.
       Think step-by-step.

    8. ✅ You MUST NOT execute fictional operations or business logic.
       ALL logic must come from tool outputs only.

    9. ✅ Your responses must be short, clear, and business-friendly. 
       Prefer bullet points for item lists.
       
    10. ✅ You Must Not create multiple Products with same product title and same product brand
    
    11. ✅ Always follow user instrunction when creating or updating items in database
    
    12. ✅ You Must Not create multiple orders with same products title and same products brand and same customer Name

    Your job is to act as the middleware between the user and the database tools, describing the results returned by the tools in natural language with NO JSON output.
    make the final answer only  like request language
"""    

HF_TOKEN=os.getenv("HF_TOKEN")

def run_smolagent(request, query, keep_memory=False):
    import json
    #llm_model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct", token=HF_TOKEN) 
    llm_model = LiteLLMModel(model_id="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    tools=[
        get_all_products, get_product_by_product_id, update_product, delete_product,
        get_advice_for_restock_products, get_all_categories, get_category_by_id, create_product,
        get_order_by_id, create_order, get_order_explanation,  build_discount_message, get_all_customers,
        get_customer_by_id, search_customers, get_product_by_product_name_or_brand,           
    ]  
    agent = CodeAgent(
        tools=tools,
        model=llm_model,
        stream_outputs=True,
        verbosity_level=1,
        additional_authorized_imports=['json'],
        max_steps = 10,
        #prompt_templates=system_prompt
    )
    print(f"agent initialized")
    prompt = f"""{system_prompt} \n\n User: {query} """
    respone = agent.run(prompt, additional_args={'request': request}, 
                        reset= not keep_memory #resest parameter is True for not saving memory, false saving memory for the same context
                        )
    print(f"Total steps in memory: {len(agent.memory.steps)}")
    if len(agent.memory.steps) > 1 and isinstance(agent.memory.steps[1], ActionStep):
        print(f"First action observation: {agent.memory.steps[1].observations[:50]}...")

    print(f"agent response: {respone}")
    return respone




