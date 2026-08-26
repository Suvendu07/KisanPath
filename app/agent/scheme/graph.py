import logging
from functools import partial
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END
from app.agent.scheme.state import GovernmentSchemeAgentState
from app.agent.scheme.nodes import (
    input_processor, intent_classifier, farmer_profile_extractor, missing_info_detector,scheme_retriever, eligibility_analyzer, response_generator, response_verifier, session_memory_updater, out_of_scope_handler, error_handler
)

logger = logging.getLogger(__name__)




def route_after_intent(state : GovernmentSchemeAgentState) -> str:
    
    """
    After intent_classifier, decide the next node:
      - Error in any previous node → error_handler
      - Out of scope → out_of_scope_handler
      - Doc/detail query with known scheme → skip profile extraction
      - Everything else → farmer_profile_extractor
    """
    if state.get("error") and not state.get("final_response"):
        return "error_handler"
    
    intent = state.get("intent", "list_schemes")
    
    if intent == "out_of_scope":
        return "out_of_scope_handler"
    
    if intent in ["document_requiremens", "scheme_details"] and state.get("specific_scheme"):
        return "scheme_retriever"
    
    return "farmer_profile_extractor"


def route_after_missing_info(state : GovernmentSchemeAgentState) -> str:
    
    """
    After missing_info_detector, decide:
      - Error → error_handler
      - Needs clarification → end (return question to user)
      - Have enough info → scheme_retriever
    """
    
    if state.get("error") and not state.get("final_response"):
        return "error_handler"
    
    if state.get("needs_clarification"):
        return "clarification_end"
    
    return "scheme_retriever"


def route_after_verification(state : GovernmentSchemeAgentState) -> str:
    """
    After response_verifier, decide:
      - Error → error_handler
      - High confidence → response_generator
      - Low confidence + no retries yet → retry scheme_retriever
      - Low confidence + already retried → response_generator (with warning)
    """
    
    if state.get("error") and not state.get("final_response"):
        return "error_handler"
    
    confidence = state.get("confidence_score", 0.7)
    retry_count = state.get("retry_count", 0)
    
    if confidence >= 0.5:
        return "response_generator"
    
    if retry_count == 0:
        return "scheme_retriever_retry"
    
    return "response_generator"


def route_after_error_check(state : GovernmentSchemeAgentState) -> str:
    """
    Generic error check after nodes that don't have their own routing.
    Used after farmer_profile_extractor and eligibility_analyzer.
    """
    
    if state.get("error") and not state.get("final_response"):
        return "error_handler"
    
    return "next"


def make_node_with_db(node_fn, db : Session):
    
    """
    Wraps a node function to inject the DB session.
    LangGraph doesn't support dependency injection natively,
    so we use functools.partial at graph build time.
    """
    
    def wrapped(state : GovernmentSchemeAgentState) -> str:
        return node_fn(state, db = db)
    
    wrapped.__name__ == node_fn.__name__
    return wrapped


def build_scheme_agent_graph(db : Session):
    """
    Builds and compiles the LangGraph state machine.
    Called once at startup with the DB session factory.
 
    Returns a compiled LangGraph app.
 
    NOTE: In production with multiple workers, call this once per
    worker process and store as a module-level singleton.
    """
    
    
    graph = StateGraph(GovernmentSchemeAgentState)
 
  
    graph.add_node("input_processor", make_node_with_db(input_processor, db))
    
    graph.add_node("intent_classifier", make_node_with_db(intent_classifier, db))
    
    graph.add_node("farmer_profile_extractor", make_node_with_db(farmer_profile_extractor, db))
    
    graph.add_node("missing_info_detector", make_node_with_db(missing_info_detector, db))
    
    graph.add_node("scheme_retriever", make_node_with_db(scheme_retriever, db))
    
    graph.add_node("scheme_retriever_retry", make_node_with_db(scheme_retriever, db))
    
    graph.add_node("eligibility_analyzer", make_node_with_db(eligibility_analyzer, db))
    
    graph.add_node("response_verifier", make_node_with_db(response_verifier, db))
    
    graph.add_node("response_generator", make_node_with_db(response_generator, db))
    
    graph.add_node("session_memory_updater", make_node_with_db(session_memory_updater, db))
    
    graph.add_node("out_of_scope_handler", make_node_with_db(out_of_scope_handler, db))
    
    graph.add_node("error_handler", make_node_with_db(error_handler, db))
    
    
    def clarification_node(state : GovernmentSchemeAgentState) -> dict:
        
        return {
            "final_response" : state.get("clarification_question", "Could you please provide more details"),
            
            "is_complete" : True,
            "needs_clarification" : True,
        }
        
    graph.add_node("clarification_end", clarification_node)
    
    def mark_retry(state : GovernmentSchemeAgentState) -> dict:
        return {"retry_count" : state.get("retry_count", 0) + 1}
    graph.add_node("mark_retry", mark_retry)
    
    
    graph.set_entry_point("input_processor")
    
    graph.add_edge("input_processor", "intent_classifier")
    
    graph.add_conditional_edges("intent_classifier", route_after_intent,
                                {
                                    "farmer_profile_extractor" : "farmer_profile_extractor",
                                    "scheme_retriever" : "scheme_retruver",
                                    "out_of_scope_handler" : "out_of_scope_handler",
                                    "error_handler" : "error_handler",
                                })
    
    graph.add_conditional_edges(
        "missing_info_detector",
        route_after_missing_info,
        {
            "scheme_retriver" : "scheme_retriever",
            "clarification_end" : "clarification_end",
            "error_handler" : "error_handler",
        }
    )
    
    graph.add_conditional_edges(
        "scheme_retriever",
        lambda state : "error_handler" if (state.get("error") and not state.get("final_response")) else "eligibility_analyzer",
        {
            "eligibilty_analyzer" : "eligibility_analyzer",
            "error_handler" : "error_handler",
        }
    )
    
    graph.add_conditional_edges(
        "eligibility_analyzer",
        lambda state : "error_handler" if (state.get("error") and not state.get("final_response"))else "response_verifier",
                                           {
                                               "response_verifier" : "response_verifier",
                                               "error_handler" : "error_handler",
                                           })
    
    graph.add_conditional_edges(
        "response_verifier",
        route_after_verification,{
            "response_generator" : "response_generator",
            "scheme_retriever_retry" : "mark_retry",
            "error_handler" : "error_handler",
        }
    )
    
    graph.add_edge("mark_retry", "scheme_retriver_retry")
    
    graph.add_edge("scheme_retriever_retry", "eligibility_analyzer")
    
    
    graph.add_edge("response_generator", "session_memory_updater")
 
    # Terminal nodes → END
    graph.add_edge("session_memory_updater", END)
    graph.add_edge("out_of_scope_handler", END)
    graph.add_edge("error_handler", END)
    graph.add_edge("clarification_end", END)
 
 
    compiled = graph.compile()
    logger.info("Government Scheme Agent graph compiled successfully.")
    return compiled