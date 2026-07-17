from typing import TypedDict, Annotated, Sequence
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
import json


from app.config import settings
from app.schemas.ai import AgentRequest, AgentResponse, AgentStep



class AgentState(TypedDict):
    messages : Annotated[Sequence[BaseMessage], lambda x,y:x+y]
    steps : list[dict]
    location : str | None
    context : str | None
    
    
    
AGENT_SYSTEM = """You are AgriAI Farming Agent — an intelligent assistant for Indian farmers.
 
You have access to these tools:
  - get_weather_tool         → get live weather for any location
  - recommend_crop_tool      → recommend best crop based on soil + weather
  - recommend_fertilizer_tool→ recommend fertilizer based on NPK and soil
  - get_price_tool           → get predicted mandi price for a crop
  - ask_knowledge_base_tool  → search farming documents for answers
 
Decision rules:
  1. If farmer mentions a location → ALWAYS call get_weather_tool first
  2. If farmer asks what to grow   → call recommend_crop_tool
  3. If farmer asks about fertilizer → call recommend_fertilizer_tool
  4. If farmer asks about price    → call get_price_tool
  5. If farmer asks a general farming question → call ask_knowledge_base_tool
  6. Combine all results into ONE clear final answer
 
Always respond in simple language. Use bullet points. End with a Pro Tip 🌱."""
 
 
 
# tools the agent can call
@tool
def get_weather_tool(location : str) -> str:
    """Get the current weather information for a given location."""

    try:
        from app.services.weather_service import get_current_weather
        w = get_current_weather(location)
        
        return json.dumps({
            "location" : w.location,
            "temp_c" : w.current.temp_c,
            "humidity" : w.current.humidity,
            "rainfall_mm" : w.current.rainfall_mm,
            "condition" : w.current.condition,
            "season" : w.season,
            "sowing_alert" : w.sowing_alert,
            "forecast" : [
                {
                    "date" : d.date,
                    "condition" : d.condition,
                    "rain_mm" : d.total_rain_mm,
                    "farming_tip" : d.farming_tip,
                }
                for d in w.forecast
            ],            
        })
        
    except Exception as e:
        return f"weather fetch failed : {str(e)}"
    
    
    

@tool
def recommend_crop_tool(nitrogen : float, phosphorus : float, potassium : float, ph : float, location : str) -> str:
    
    """Recommend the best crop based on soil nutrients and weather."""
    try:
        from app.services.weather_service import get_weather_for_crop_recommendation
        from app.services.ml_service import recommend_crop
        from app.schemas.ai import CropRecommendRequest
        
        
        weather = get_weather_for_crop_recommendation(location)
        payload = CropRecommendRequest(
            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            ph=ph,
            location=location,
        )
        
        result = recommend_crop(payload)
        
        if not result.model_ready:
            return (
                f"Crop recommendation model is not yet loaded. "
                f"Based on season ({weather['season']}) and NPK values, "
                f"consider crops like Rice (Kharif), Wheat (Rabi), or Maize."
            )
            
            
        return json.dumps({
            "recommended_crop" : result.recommended_crop,
            "confidence" : result.confidence,
            "top_3" : result.top_3_crops,
            "growing_tips" : result.growing_tips,
            "best_season" : result.best_season,
        })
        
    except Exception as e:
        return f"Crop recommendation failed: {str(e)}"
    
    
    


@tool
def recommend_fertilizer_tool(crop_name : str,nitrogen : float, phosphorus : float, potassium : float, soil_type : str) -> str:
    """Recommend fertilizer based on crop, soil type, and NPK values."""
    try:
        from app.services.ml_service import recommend_fertilizer_rule_based
        
        result = recommend_fertilizer_rule_based(
            crop_name = crop_name,
            nitrogen = nitrogen,
            phosphorus = phosphorus,
            potassium = potassium,
            soil_type = soil_type,
        )
        
        return json.dumps(result)
    
    except Exception as e:
        return f"Fertilizer recommendation failed: {str(e)}"
    
    
    
@tool
def get_price_tool(crop_name : str, state : str) -> str:
    """Predict mandi price for a crop."""
    try:
        from app.services.ml_service import predict_price
        from datetime import datetime
        from app.schemas.ai import PricePredictionRequest
        
        
        now = datetime.now()
        payload = PricePredictionRequest(
            crop_name= crop_name,
            state= state,
            month=now.month,
            year = now.year,
        )
        
        result = predict_price(payload)
        
        
        if not result.model_today:
            return(
                f"Price prediction model is not loaded."
                f"Check current rates at agmarknet.gov.in for {crop_name} in {state}."
            )
            
            
        return json.dumps({
            "crops" : result.crop_name,
            "state" : result.state,
            "predicted_price" : result.predicted_price,
            "price_range" : result.price_range,
            "trend" : result.trend,
            "note" : result.note,
        }
        )
        
        
    except Exception as e:
        return f"Price predication failed : {str(e)}"



@tool
def ask_knowledge_base_tool(question : str) -> str:
    
    """Search the farming knowledge base for an answer."""
    try:
        from app.services.rag_service import ask_farming_docs
        from app.schemas.ai import RagRequest
        
        result = ask_farming_docs(RagRequest(question=question))
        return result.answer
    
    except Exception as e:
        return f"knowledge base search failed: {str(e)}. Try asking AgriAI chatbot instead."
    
    
    
ALL_TOOLS = [
    get_weather_tool, recommend_crop_tool, recommend_fertilizer_tool, get_price_tool, ask_knowledge_base_tool
]


def build_agent_graph():
    
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured.")
    
    
    llm = ChatGoogleGenerativeAI(
        model = "gemini-2.5-flash",
        google_api_key = settings.GEMINI_API_KEY,
        temperature = 0.5,
        ).bind_tools(ALL_TOOLS)
    
    
    def agent_node(state : AgentState) -> AgentState:
        
        messages = [SystemMessage(content=AGENT_SYSTEM)] + list(state["messages"])
        response = llm.invoke(messages)
        
        
        step = {
            "step_name" : "agent_reasoning",
            "input" : state["messages"][-1].content if state["messages"] else "",
            "output" : response.content or "(calling tool...)",
            "tool_used" : None
        }
        
        
        return {
            "messages" : [response],
            "steps" : state.get("steps", []) + [step],
        }
        
        
    tool_node = ToolNode(ALL_TOOLS)
    
    
    def tool_with_tracking(state : AgentState) -> AgentState:
        
        result = tool_node.invoke(state)
        last_msg = state["messages"][-1]
        tool_calls = getattr(last_msg, "tool_calls", [])
        
        steps = state.get("steps", [])
        for call in tool_calls:
            steps.append({
                "step_name" : "tool_execution",
                "input" : str(call.get("args", {})),
                "output" : str(result["messages"][-1].content)[:300],
                "tool_used" : call.get("name", "unknown"),
            })
            
            
        return {**result, "steps" : steps}
    
    
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_with_tracking)
    graph.set_entry_point("agent")
    
    
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    
    
    return graph.compile()



def run_farming_agent(payload : AgentRequest) -> AgentResponse:
    
    user_message = payload.query
    
    if payload.location:
        user_message += f"\n\n[My location : {payload.location}]"
        
    if payload.context:
        user_message += f"\n[Additional context: {payload.context}]"
        
        
    initial_state : AgentState = {
        "messages" : [HumanMessage(content=user_message)],
        "steps" : [],
        "location" : payload.location,
        "context" : payload.context,
    }
    
    
    
    try:
        graph = build_agent_graph()
        
        final_state  = graph.invoke(initial_state, {"recursion_limit": 10})
   
    except ValueError as e:
        raise ValueError(str(e))
    except Exception as e:
        raise RuntimeError(f"Agent error: {str(e)}")
 
    # Extract final answer from last AI message
    final_answer = ""
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            final_answer = msg.content
            break
 
    steps = [AgentStep(**s) for s in final_state.get("steps", [])]
 
    return AgentResponse(
        final_answer = final_answer or "Agent could not produce a final answer. Please try rephrasing.",
        steps        = steps,
        total_steps  = len(steps),
    )