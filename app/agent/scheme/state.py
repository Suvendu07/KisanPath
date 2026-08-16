from typing import TypedDict, Annotated, Optional
from langchain_core.messages import BaseMessage
import operator


class GovernmentSchemeAgentState(TypedDict):
    
    user_id : int
    user_role : str
    session_id : str

    
    messages : Annotated[list[BaseMessage], operator.add]
    current_query : str
    conversation_history : list
    conversation_turn : int

    farmer_name : Optional[str]
    farmer_state : Optional[str]
    farmer_district : Optional[str]
    land_size_acres : Optional[float]
    crop_types : Optional[list]
    farmer_category : Optional[str]
    annual_income : Optional[str]
    has_bank_account : Optional[bool]
    has_aadhhar : Optional[bool]
    kisan_id : Optional[str]
    
    intent : Optional[str]
    specific_scheme : Optional[str]
    specific_topic : Optional[str]
    
    missing_fields : list
    clarification_question : Optional[str]
    clarification_attempts : int

    raw_rag_results : list
    rag_sources : list
    candidate_schemes : list

    eligible_schemes : list
    conditional_schemes : list
    ineligible_schemes : list

    verification_passed : bool
    hallucination_flags : list
    confidence_score : float
    retry_count : int

    final_response : Optional[str]
    follow_up_question : list
    disclaimer : str

    next_node : Optional[str]
    error : Optional[str]
    error_node : Optional[str]
    is_complete : bool
    needs_clarificatoin : bool
    steps_taken : list



def create_initial_state(
    user_id: int,
    user_role: str,
    session_id: str,
    current_query: str,
) -> GovernmentSchemeAgentState:
    """
    Creates the initial state for a new agent invocation.
    History and farmer_profile will be populated by input_processor
    from the DB after this is created.
    """
    
    return GovernmentSchemeAgentState(
        # Identity
        user_id = user_id,
        user_role = user_role,
        session_id = session_id,
        # Conversation
        messages = [],
        current_query = current_query,
        conversation_history = [],
        conversation_turn  = 0,
        # Farmer profile — all None, filled by nodes
        farmer_name = None,
        farmer_state = None,
        farmer_district = None,
        land_size_acres = None,
        crop_types = None,
        farmer_category = None,
        annual_income = None,
        has_bank_account = None,
        has_aadhaar = None,
        kisan_id = None,
        # Intent
        intent = None,
        specific_scheme = None,
        specific_topic = None,
        # Missing info
        missing_fields = [],
        clarification_question  = None,
        clarification_attempts  = 0,
        # Retrieved schemes
        raw_rag_results = [],
        rag_sources = [],
        candidate_schemes = [],
        # Eligibility
        eligible_schemes = [],
        conditional_schemes= [],
        ineligible_schemes = [],
        # Verification
        verification_passed  = False,
        hallucination_flags  = [],
        confidence_score = 0.0,
        retry_count = 0,
        # Output
        final_response = None,
        follow_up_questions  = [],
        disclaimer = (
            "⚠️ Scheme details and eligibility criteria may have changed. "
            "Always verify with your nearest Krishi Vigyan Kendra (KVK) "
            "or visit the official scheme portal before applying."
        ),
        # Control flow
        next_node = None,
        error = None,
        error_node = None,
        is_complete = False,
        needs_clarification  = False,
        steps_taken = [],
    )
 