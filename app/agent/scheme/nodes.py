import json
import time
import logging
from typing import Any


from app.core.llm import get_strict_llm, get_creative_llm
from app.core.agent_memory import (
    load_session, save_session, log_tool_call, build_history_context,
)
from app.agent.scheme.state import GovernmentSchemeAgentState
from app.agent.scheme.prompts import (
    intent_clasification_prompt, farmer_profile_extraction_prompt, missing_info_prompt, build_retrieval_query, eligibility_analysis_prompt, verification_prompt, response_generation_prompt, OUT_OF_SCOPE_RESPONSE, error_response,
)

from app.agent.scheme.tools import (get_farmer_profile_from_db,faiss_retrieve_schemes,get_state_scheme_context, call_gemini_for_json, call_gemini_for_text,)




logger = logging.getLogger(__name__)

AGENT_NAME = "goverment_scheme_agent"

def input_processor(state : GovernmentSchemeAgentState, db = None) -> dict:
    """
    Entry point — loads session + DB profile, prepares state for processing.
    Always the first node to run. Pure Python, no LLM calls.
    """
    
    start = time.time()
    try:
        session_data = {}
        db_profile = {}
        
        if db:
            session_data = load_session(
                session_id = state["session_id"],
                user_id = state["user_id"],
                agent_name = AGENT_NAME,
                db = db,
            )
            # Load farmer profile from existing farmers table
            db_profile = get_farmer_profile_from_db(state["user_id"], db)
            
        history      = session_data.get("history", [])
        saved_profile = session_data.get("farmer_profile", {})
        turn_count   = session_data.get("turn_count", 0) + 1
        
        merged_profile = {**db_profile, **saved_profile}

        
        update = {
            "conversation_history":  history,
            "conversation_turn": turn_count,
            "steps_taken": state.get("steps_taken", []) + ["input_processor"],
            # Fill farmer profile from DB + session
            "farmer_name": merged_profile.get("farmer_name"),
            "farmer_state": merged_profile.get("farmer_state"),
            "farmer_district": merged_profile.get("farmer_district"),
            "land_size_acres": merged_profile.get("land_size_acres"),
            "crop_types": merged_profile.get("crop_types"),
            "farmer_category": merged_profile.get("farmer_category"),
            "annual_income": merged_profile.get("annual_income"),
            "has_bank_account": merged_profile.get("has_bank_account"),
            "has_aadhaar": merged_profile.get("has_aadhaar"),
            "kisan_id": merged_profile.get("kisan_id"),
        }
        
        
        if db:
            log_tool_call(
                session_id = state["session_id"],
                agent_name = AGENT_NAME,
                node_name     = "input_processor",
                db            = db,
                input_summary = f"user_id={state['user_id']}",
                output_summary= f"loaded session turn={turn_count}",
                duration_ms   = (time.time() - start) * 1000,
            )
        
        return update
    
    except Exception as e:
        logger.error(f"input_processor failed : {e}")
        
        return {
            "error" : str(e),
            "error_node" : input_processor,
            "steps_taken" : state.get("steps_taken", []) + ["input_processor"],
        }
        



def intent_classifier(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Classifies query into one of 7 intents using strict Gemini call.
    Extracts specific_scheme and specific_topic if mentioned.
    """
    start = time.time()
    try:
        llm = get_strict_llm()
        history_ctx = build_history_context(state.get("conversation_history", []))
 
        prompt  = intent_clasification_prompt(state["current_query"], history_ctx)
        result  = call_gemini_for_json(prompt, llm)
 
        if not result:
            # Fallback if JSON parse fails
            result = {
                "intent":          "list_schemes",
                "specific_scheme": None,
                "specific_topic":  None,
            }
            
        update = {
            "intent": result.get("intent", "list_schemes"),
            "specific_scheme": result.get("specific_scheme"),
            "specific_topic":  result.get("specific_topic"),
            "steps_taken": state.get("steps_taken", []) + ["intent_classifier"],
        }
        
        
        if db:
            log_tool_call(
                session_id = state["session_id"],
                agent_name = AGENT_NAME,
                node_name = "intent_classifier",
                db = db,
                input_summary  = state["current_query"][:200],
                output_summary = f"intent={update['intent']}",
                duration_ms = (time.time() - start) * 1000,
            )
 
        return update
    
    except Exception as e:
        logger.error(f"intent_classifier failed: {e}")
        return {
            "intent": "list_schemes",   # safe fallback
            "error": str(e),
            "error_node": "intent_classifier",
            "steps_taken": state.get("steps_taken", []) + ["intent_classifier"],
        }
        
        


def farmer_profile_extractor(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Extracts farmer info from current query + conversation history using NLP.
    Merges with existing profile — never overwrites known values.
    """
    start = time.time()
    try:
        llm = get_strict_llm()
        history_ctx = build_history_context(state.get("conversation_history", []))
 
        prompt  = farmer_profile_extraction_prompt(state["current_query"], history_ctx)
        result  = call_gemini_for_json(prompt, llm)
 
        if not result:
            return {
                "steps_taken": state.get("steps_taken", []) + ["farmer_profile_extractor"]
            }
 
        # Only update fields that are currently None in state
        update = {"steps_taken": state.get("steps_taken", []) + ["farmer_profile_extractor"]}
 
        for field in [
            "farmer_name", "farmer_state", "farmer_district",
            "land_size_acres", "crop_types", "farmer_category",
            "annual_income", "has_bank_account", "has_aadhaar",
        ]:
            extracted = result.get(field)
            current   = state.get(field)
            # Only fill if extracted has a value and state doesn't already have one
            if extracted is not None and current is None:
                update[field] = extracted
 
        # Derive category from land size if still missing
        land  = update.get("land_size_acres") or state.get("land_size_acres")
        cat   = update.get("farmer_category") or state.get("farmer_category")
        if land and not cat:
            if land < 1.0:
                update["farmer_category"] = "marginal"
            elif land <= 2.0:
                update["farmer_category"] = "small"
            else:
                update["farmer_category"] = "large"
 
        if db:
            log_tool_call(
                session_id= state["session_id"],
                agent_name= AGENT_NAME,
                node_name= "farmer_profile_extractor",
                db= db,
                input_summary  = state["current_query"][:200],
                output_summary = str({k: v for k, v in update.items()
                                       if k != "steps_taken"})[:300],
                duration_ms= (time.time() - start) * 1000,
            )
 
        return update
 
    except Exception as e:
        logger.error(f"farmer_profile_extractor failed: {e}")
        return {
            "error":str(e),
            "error_node": "farmer_profile_extractor",
            "steps_taken": state.get("steps_taken", []) + ["farmer_profile_extractor"],
        }
 
 

def missing_info_detector(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Determines what info is still needed and whether to ask for it.
    Max 2 clarification rounds — then proceeds with available info.
    """
    start = time.time()
    try:
        llm = get_strict_llm()
 
        # Build current profile dict from state
        current_profile = {
            "farmer_name":state.get("farmer_name"),
            "farmer_state":state.get("farmer_state"),
            "farmer_district": state.get("farmer_district"),
            "land_size_acres": state.get("land_size_acres"),
            "crop_types":state.get("crop_types"),
            "farmer_category": state.get("farmer_category"),
            "annual_income":state.get("annual_income"),
            "specific_scheme": state.get("specific_scheme"),
            "specific_topic":state.get("specific_topic"),
        }
 
        prompt = missing_info_prompt(
            intent= state.get("intent", "list_schemes"),
            farmer_profile= current_profile,
            clarification_attempts = state.get("clarification_attempts", 0),
        )
        result = call_gemini_for_json(prompt, llm)
 
        if not result:
            return {
                "missing_fields":   [],
                "needs_clarification": False,
                "steps_taken": state.get("steps_taken", []) + ["missing_info_detector"],
            }
 
        missing  = result.get("missing_fields", [])
        should_ask = result.get("should_ask", False)
        question= result.get("clarification_question")
        attempts= state.get("clarification_attempts", 0)
 
        # Enforce max 2 rounds
        if attempts >= 2:
            should_ask = False
            missing= []
            question   = None
 
        update = {
            "missing_fields":missing,
            "clarification_question":  question,
            "needs_clarification":should_ask and bool(missing),
            "steps_taken": state.get("steps_taken", []) + ["missing_info_detector"],
        }
 
        if should_ask and missing:
            update["clarification_attempts"] = attempts + 1
 
        if db:
            log_tool_call(
                session_id = state["session_id"],
                agent_name = AGENT_NAME,
                node_name= "missing_info_detector",
                db= db,
                output_summary = f"missing={missing} ask={should_ask}",
                duration_ms    = (time.time() - start) * 1000,
            )
 
        return update
 
    except Exception as e:
        logger.error(f"missing_info_detector failed: {e}")
        return {
            "missing_fields":    [],
            "needs_clarification": False,
            "error":      str(e),
            "error_node": "missing_info_detector",
            "steps_taken": state.get("steps_taken", []) + ["missing_info_detector"],
        }
 
 

def scheme_retriever(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Builds enriched semantic query and retrieves scheme chunks from FAISS.
    Also fetches state-specific mandi data for context.
    """
    start = time.time()
    try:
        # Build enriched query from state
        enriched_query = build_retrieval_query(
            intent = state.get("intent", "list_schemes"),
            farmer_state = state.get("farmer_state"),
            crop_types = state.get("crop_types"),
            farmer_category = state.get("farmer_category"),
            specific_scheme = state.get("specific_scheme"),
            specific_topic  = state.get("specific_topic"),
        )
 
        chunks, sources = faiss_retrieve_schemes(enriched_query, top_k=6)
 
        # Get mandi context if DB available
        mandi_context = ""
        if db and state.get("farmer_state"):
            mandi_context = get_state_scheme_context(state.get("farmer_state"), db)
 
        # Combine chunks with mandi context
        all_content = chunks[:]
        if mandi_context:
            all_content.append(mandi_context)
 
        update = {
            "raw_rag_results":  all_content,
            "rag_sources":      sources,
            "steps_taken": state.get("steps_taken", []) + ["scheme_retriever"],
        }
 
        if db:
            log_tool_call(
                session_id = state["session_id"],
                agent_name = AGENT_NAME,
                node_name = "scheme_retriever",
                tool_name= "faiss_retriever",
                db = db,
                input_summary  = enriched_query[:300],
                output_summary = f"retrieved {len(chunks)} chunks, {len(sources)} sources",
                duration_ms    = (time.time() - start) * 1000,
            )
 
        return update
 
    except Exception as e:
        logger.error(f"scheme_retriever failed: {e}")
        return {
            "raw_rag_results": [],
            "rag_sources":     [],
            "error":      str(e),
            "error_node": "scheme_retriever",
            "steps_taken": state.get("steps_taken", []) + ["scheme_retriever"],
        }
 
 

def eligibility_analyzer(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Filters retrieved schemes based on farmer's profile.
    Produces eligible, conditional, and ineligible lists.
    """
    start = time.time()
    try:
        llm = get_strict_llm()
 
        raw_chunks = state.get("raw_rag_results", [])
        if not raw_chunks:
            return {
                "eligible_schemes": [],
                "conditional_schemes": [],
                "ineligible_schemes":  [],
                "candidate_schemes":   [],
                "steps_taken": state.get("steps_taken", []) + ["eligibility_analyzer"],
            }
 
        rag_content = "\n\n---\n\n".join(raw_chunks[:5])   # cap tokens
 
        farmer_profile = {
            "state": state.get("farmer_state"),
            "district": state.get("farmer_district"),
            "land_size_acres":  state.get("land_size_acres"),
            "crop_types": state.get("crop_types"),
            "farmer_category":  state.get("farmer_category"),
            "annual_income": state.get("annual_income"),
            "has_bank_account": state.get("has_bank_account"),
            "has_aadhaar": state.get("has_aadhaar"),
            "kisan_id":state.get("kisan_id"),
        }
 
        prompt = eligibility_analysis_prompt(rag_content, farmer_profile)
        result = call_gemini_for_json(prompt, llm)
 
        if not result:
            # Fallback — return all chunks as unanalyzed candidates
            return {
                "eligible_schemes":    [],
                "conditional_schemes": [{"name": "Unable to analyze — please check with KVK"}],
                "ineligible_schemes":  [],
                "steps_taken": state.get("steps_taken", []) + ["eligibility_analyzer"],
            }
 
        update = {
            "eligible_schemes": result.get("eligible_schemes", []),
            "conditional_schemes": result.get("conditional_schemes", []),
            "ineligible_schemes":  result.get("ineligible_schemes", []),
            "candidate_schemes":   (
                result.get("eligible_schemes", []) +
                result.get("conditional_schemes", [])
            ),
            "steps_taken": state.get("steps_taken", []) + ["eligibility_analyzer"],
        }
 
        if db:
            log_tool_call(
                session_id= state["session_id"],
                agent_name= AGENT_NAME,
                node_name = "eligibility_analyzer",
                db = db,
                output_summary = (
                    f"eligible={len(update['eligible_schemes'])} "
                    f"conditional={len(update['conditional_schemes'])}"
                ),
                duration_ms = (time.time() - start) * 1000,
            )
 
        return update
 
    except Exception as e:
        logger.error(f"eligibility_analyzer failed: {e}")
        return {
            "eligible_schemes":    [],
            "conditional_schemes": [],
            "ineligible_schemes":  [],
            "error":      str(e),
            "error_node": "eligibility_analyzer",
            "steps_taken": state.get("steps_taken", []) + ["eligibility_analyzer"],
        }
 
 

def response_verifier(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Verifies eligible schemes against retrieved sources.
    Prevents hallucination before final response is generated.
    """
    start = time.time()
    try:
        llm = get_strict_llm()
 
        eligible = state.get("eligible_schemes", [])
        rag_sources = state.get("rag_sources", [])
        raw_chunks  = state.get("raw_rag_results", [])
 
        # If nothing was retrieved, low confidence by default
        if not raw_chunks:
            return {
                "verification_passed": False,
                "hallucination_flags": ["No source documents retrieved"],
                "confidence_score":    0.3,
                "steps_taken": state.get("steps_taken", []) + ["response_verifier"],
            }
 
        # Build sources text for verification
        rag_sources_text = "\n\n".join(raw_chunks[:4])
 
        # Build what we're about to say
        response_preview = json.dumps(eligible, indent=2)
 
        prompt  = verification_prompt(response_preview, rag_sources_text)
        result  = call_gemini_for_json(prompt, llm)
 
        if not result:
            # Can't verify — moderate confidence
            return {
                "verification_passed": True,
                "hallucination_flags": [],
                "confidence_score":    0.6,
                "steps_taken": state.get("steps_taken", []) + ["response_verifier"],
            }
 
        update = {
            "verification_passed": result.get("verification_passed", True),
            "hallucination_flags": result.get("hallucination_flags", []),
            "confidence_score": result.get("confidence_score", 0.7),
            "steps_taken": state.get("steps_taken", []) + ["response_verifier"],
        }
 
        if db:
            log_tool_call(
                session_id = state["session_id"],
                agent_name = AGENT_NAME,
                node_name = "response_verifier",
                db= db,
                output_summary = (
                    f"passed={update['verification_passed']} "
                    f"confidence={update['confidence_score']:.2f} "
                    f"flags={len(update['hallucination_flags'])}"
                ),
                duration_ms    = (time.time() - start) * 1000,
            )
 
        return update
 
    except Exception as e:
        logger.error(f"response_verifier failed: {e}")
        return {
            "verification_passed": True,    # safe default — let response generate
            "hallucination_flags": [],
            "confidence_score":    0.5,
            "error":      str(e),
            "error_node": "response_verifier",
            "steps_taken": state.get("steps_taken", []) + ["response_verifier"],
        }
 
 

def response_generator(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Generates the final personalized response using Gemini.
    Includes eligibility reasoning, documents, how-to-apply, and sources.
    """
    start = time.time()
    try:
        llm = get_creative_llm()
        history_ctx = build_history_context(state.get("conversation_history", []))
 
        farmer_profile = {
            "name":state.get("farmer_name", "Farmer"),
            "state":state.get("farmer_state", "Not specified"),
            "land":f"{state.get('land_size_acres', 'Unknown')} acres",
            "crops":state.get("crop_types", ["Not specified"]),
            "category": state.get("farmer_category", "Not specified"),
        }
 
        prompt = response_generation_prompt(
            farmer_profile = farmer_profile,
            eligible_schemes = state.get("eligible_schemes", []),
            conditional_schemes = state.get("conditional_schemes", []),
            rag_sources = state.get("rag_sources", []),
            intent = state.get("intent", "list_schemes"),
            specific_scheme= state.get("specific_scheme"),
            confidence_score = state.get("confidence_score", 0.7),
            history_context = history_ctx,
        )
 
        response_text = call_gemini_for_text(prompt, llm)
 
        if not response_text:
            response_text = (
                "I found some relevant schemes but had trouble generating a detailed response. "
                "Please try again or contact your nearest KVK office."
            )
 
        # Append standard disclaimer
        full_response = (
            response_text
            + "\n\n"
            + state.get("disclaimer", "")
        )
 
        update = {
            "final_response":  full_response,
            "is_complete": True,
            "steps_taken": state.get("steps_taken", []) + ["response_generator"],
        }
 
        if db:
            log_tool_call(
                session_id = state["session_id"],
                agent_name = AGENT_NAME,
                node_name = "response_generator",
                db = db,
                output_summary = full_response[:200],
                duration_ms = (time.time() - start) * 1000,
            )
 
        return update
 
    except Exception as e:
        logger.error(f"response_generator failed: {e}")
        return {
            "final_response": error_response("general"),
            "is_complete": True,
            "error": str(e),
            "error_node": "response_generator",
            "steps_taken": state.get("steps_taken", []) + ["response_generator"],
        }
 
 


def session_memory_updater(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Persists updated conversation history and farmer profile to PostgreSQL.
    Always the last node. Never blocks the response.
    """
    try:
        if not db:
            return {
                "steps_taken": state.get("steps_taken", []) + ["session_memory_updater"]
            }
 
        # Build updated history
        history = list(state.get("conversation_history", []))
        history.append({"role": "human", "content": state["current_query"]})
        if state.get("final_response"):
            history.append({"role": "ai", "content": state["final_response"]})
 
        # Keep only last 20 messages (10 exchanges)
        if len(history) > 20:
            history = history[-20:]
 
        # Build updated farmer profile for persistence
        farmer_profile = {
            k: state.get(k) for k in [
                "farmer_name", "farmer_state", "farmer_district",
                "land_size_acres", "crop_types", "farmer_category",
                "annual_income", "has_bank_account", "has_aadhaar", "kisan_id",
            ]
            if state.get(k) is not None
        }
 
        save_session(
            session_id = state["session_id"],
            agent_name = AGENT_NAME,
            user_id = state["user_id"],
            history = history,
            farmer_profile = farmer_profile,
            turn_count = state.get("conversation_turn", 1),
            db = db,
        )
 
        return {
            "conversation_history": history,
            "steps_taken": state.get("steps_taken", []) + ["session_memory_updater"],
        }
 
    except Exception as e:
        logger.error(f"session_memory_updater failed: {e}")
        return {
            "steps_taken": state.get("steps_taken", []) + ["session_memory_updater"]
        }
 
 

def out_of_scope_handler(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Handles non-scheme queries gracefully. Redirects to AgriAI chatbot.
    """
    return {
        "final_response": OUT_OF_SCOPE_RESPONSE,
        "is_complete": True,
        "steps_taken": state.get("steps_taken", []) + ["out_of_scope_handler"],
    }
 
 

def error_handler(state: GovernmentSchemeAgentState, db=None) -> dict:
    """
    Catches any node failure and returns a safe user-friendly message.
    Never exposes technical errors to the farmer.
    """
    error_node = state.get("error_node", "unknown")
    logger.error(
        f"error_handler triggered from node={error_node}: {state.get('error')}"
    )
 
    error_type_map = {
        "scheme_retriever": "rag_unavailable",
        "intent_classifier": "llm_unavailable",
        "response_generator": "llm_unavailable",
        "input_processor":  "db_unavailable",
    }
    error_type = error_type_map.get(error_node, "general")
 
    return {
        "final_response": error_response(error_type),
        "is_complete": True,
        "steps_taken": state.get("steps_taken", []) + ["error_handler"],
    }