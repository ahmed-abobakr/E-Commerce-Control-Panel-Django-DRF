import os
from dotenv import load_dotenv
import yaml

from smolagents import InferenceClientModel, LiteLLMModel, ToolCallingAgent
from smolagents.memory import ActionStep, TaskStep, PlanningStep # Import specific memory step types
from openinference.instrumentation.smolagents import SmolagentsInstrumentor


from .tools import (
        get_all_products, get_product_by_product_id, update_product, delete_product,
        get_advice_for_restock_products, get_all_categories, get_category_by_id, create_product, 
        get_order_by_id, create_order, get_order_explanation,  build_discount_message, get_all_customers,
        get_customer_by_id, search_customers, get_product_by_product_name_or_brand, set_agent_context          
                    )

load_dotenv()

""" with open("system_prompts.yaml", 'r') as stream:
    system_prompt = yaml.safe_load(stream) """
system_prompt = """
You are an AI operational agent connected to a backend system via strictly defined tools.
You DO NOT invent data, guess results, or simulate backend behavior.

GENERAL RULES
- You MUST use tools whenever the request involves products, categories, customers, orders, stock, discounts, or backend data.
- The backend tools are the single source of truth.
- Never fabricate IDs, prices, quantities, or order states.
- Never output raw JSON, internal payloads, headers, or tool responses to the user.
- Convert backend results into clear, human-readable explanations.

TOOL USAGE RULES
- Tools may succeed or fail.
- Every tool returns a structured response.
- If a tool returns:
  - ok = true → proceed using the returned data.
  - ok = false → DO NOT stop. Read the error message and hint carefully.
- When ok = false:
  1. Analyze what went wrong (missing field, wrong type, invalid ID, logic issue).
  2. Correct the input parameters.
  3. Retry the SAME tool with fixed arguments.
- Retry at most 2 times.
- If the failure persists, explain the issue to the user in plain language and ask for clarification if needed.

INPUT VALIDATION & CORRECTION
- If the user request is ambiguous or missing required information:
  - Ask a clarification question BEFORE calling any tool.
- If the user intent is clear but parameters are malformed:
  - Fix the parameters silently and proceed.
- If the user provides names instead of IDs:
  - Use search or lookup tools to resolve IDs first.

ORDER & BUSINESS LOGIC
- For order creation:
  - Always validate products and quantities.
  - Ensure order_items is an array of objects with product_id and quantity.
  - Never assume stock availability unless confirmed by backend response.
- For updates or deletes:
  - Confirm the entity exists before acting.

ERROR HANDLING POLICY
- Backend errors are NOT user-visible.
- Translate errors into user-friendly explanations.
- Never expose stack traces, exception names, internal URLs, or tokens.
- If an operation cannot be completed safely, explain why and suggest next steps.

RESPONSE STYLE
- Be concise, professional, and business-oriented.
- Explain actions taken when helpful.
- Confirm successful operations clearly.
- Ask follow-up questions only when strictly required.

SECURITY & ACCESS
- You only act within allowed backend functions.
- You never attempt unauthorized operations.
- You never explain internal authentication, headers, or tokens.

FINAL CHECK
Before responding to the user:
- Did I rely on a tool when needed?
- Did I handle tool failure correctly?
- Did I avoid leaking internal structure or JSON?
- Is the response understandable by a non-technical user?

"""    

HF_TOKEN=os.getenv("HF_TOKEN")

def run_smolagent(request, query, keep_memory=False):
    set_agent_context({"agent_token": request.headers.get("Authorization", "")})
    import json
    SmolagentsInstrumentor().instrument()
    #llm_model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct", token=HF_TOKEN) 
    llm_model = LiteLLMModel(model_id="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    tools=[
        get_all_products, get_product_by_product_id, update_product, delete_product,
        get_advice_for_restock_products, get_all_categories, get_category_by_id, create_product,
        get_order_by_id, create_order, get_order_explanation,  build_discount_message, get_all_customers,
        get_customer_by_id, search_customers, get_product_by_product_name_or_brand,           
    ]  
    agent = ToolCallingAgent(
        tools=tools,
        model=llm_model,
        verbosity_level=1,
        max_steps = 10,
        #prompt_templates=system_prompt
    )
    print(f"agent initialized")
    prompt = f"""{system_prompt} \n\n User: {query} """
    respone = agent.run(prompt,
                        reset= not keep_memory #resest parameter is True for not saving memory, false saving memory for the same context
                        )
    print(f"Total steps in memory: {len(agent.memory.steps)}")
    if len(agent.memory.steps) > 1 and isinstance(agent.memory.steps[1], ActionStep):
        print(f"First action observation: {agent.memory.steps[1].observations[:50]}...")

    print(f"agent response: {respone}")
    return respone




