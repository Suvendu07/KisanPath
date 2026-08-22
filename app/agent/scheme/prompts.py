from typing import Optional

def intent_clasification_prompt(query: str, history_context : str) -> str:
    
    return f"""You are an intent classifier for KisanPath's Government Scheme Agent.
 
Your ONLY job is to classify the farmer's query into exactly one of these intents:
 
INTENTS:
  list_schemes → farmer wants to know which schemes exist
  eligibility_check → farmer wants to know if they qualify for something
  document_requirements → farmer asks what documents are needed
  application_process → farmer asks how to apply
  subsidy_query → farmer asks about subsidies or financial benefits
  scheme_detail → farmer wants detailed info about one specific scheme
  out_of_scope → query is NOT about government agriculture schemes
 
RULES:
  - Output ONLY a JSON object, nothing else
  - JSON must have: intent, specific_scheme (or null), specific_topic (or null)
  - specific_scheme: name if farmer mentioned one (e.g. "PM-KISAN", "PMFBY")
  - specific_topic: topic area if mentioned (e.g. "irrigation", "insurance", "seeds")
 
EXAMPLES:
  Query: "What schemes are available for farmers?"
  Output: {{"intent": "list_schemes", "specific_scheme": null, "specific_topic": null}}
 
  Query: "I am a small farmer from Odisha. Am I eligible for PM-KISAN?"
  Output: {{"intent": "eligibility_check", "specific_scheme": "PM-KISAN", "specific_topic": null}}
 
  Query: "What documents do I need for PMFBY?"
  Output: {{"intent": "document_requirements", "specific_scheme": "PMFBY", "specific_topic": null}}
 
  Query: "Is there any subsidy for drip irrigation?"
  Output: {{"intent": "subsidy_query", "specific_scheme": null, "specific_topic": "irrigation"}}
 
  Query: "What is today's weather?"
  Output: {{"intent": "out_of_scope", "specific_scheme": null, "specific_topic": null}}
 
CONVERSATION HISTORY (for context):
{history_context if history_context else "No previous conversation."}
 
FARMER'S QUERY:
{query}
 
Output (JSON only, no explanation, no markdown):"""




def farmer_profile_extraction_prompt(query : str, history_context : str) -> str:
    
    return f"""You are extracting farmer profile information from a conversation.
 
Extract ONLY information that is explicitly mentioned. Do NOT guess or assume.
Output a JSON object with these exact fields (use null if not mentioned):
 
{{
  "farmer_name": null or "string",
  "farmer_state": null or "state name in English",
  "farmer_district":  null or "district name",
  "land_size_acres": null or number (convert hectares to acres if needed: 1 ha = 2.47 acres),
  "crop_types": null or ["crop1", "crop2"],
  "farmer_category":  null or "small" or "marginal" or "large",
  "annual_income": null or "string description",
  "has_bank_account": null or true or false,
  "has_aadhaar": null or true or false
}}
 
FARMER CATEGORY RULES (if land size is given):
  marginal farmer = less than 1 acre
  small farmer = 1 to 2 acres
  large farmer = more than 2 acres
 
CONVERSATION HISTORY:
{history_context if history_context else "No previous conversation."}
 
CURRENT QUERY:
{query}
 
Output (JSON only, no explanation):"""




def missing_info_prompt(intent : str, farmer_profile : dict, clarification_attempts : int,) -> str:
    
    return f"""You are helping determine what information is needed to answer a farmer's query.
 
INTENT: {intent}
CURRENT FARMER PROFILE: {farmer_profile}
CLARIFICATION ATTEMPTS SO FAR: {clarification_attempts}
 
REQUIRED FIELDS PER INTENT:
  list_schemes → minimum: farmer_state
  eligibility_check → required: farmer_state, land_size_acres, crop_types, farmer_category
  document_requirements → required: specific_scheme (already known from intent)
  application_process   → required: specific_scheme
  subsidy_query → required: farmer_state, specific_topic
  scheme_detail → required: specific_scheme
 
RULES:
  - List only fields that are null/missing in the current profile
  - If clarification_attempts >= 2, return empty missing_fields (stop asking)
  - Ask for the MOST IMPORTANT missing field only
  - Write the clarification question in simple Hindi-English (Hinglish) or English
  - Question must be friendly and short (one sentence)
 
Output a JSON object:
{{
  "missing_fields": ["field1", "field2"],
  "clarification_question": "string or null",
  "should_ask": true or false
}}
 
Output (JSON only):"""




def build_retrieval_query(intent : str, farmer_state : Optional[str], crop_types : Optional[list],farmer_category : Optional[str], specific_schema : Optional[str], specific_topic : Optional[str],) -> str:
    
    """Builds an enriched semantic query for FAISS retrieval.
    Much better results than passing the raw user message."""
    
    parts = ["Indian goverment agriculture schemas"]
    
    if specific_schema:
        parts.append(specific_schema)
        
    if specific_topic:
        parts.append(f"{specific_topic} subsidy support")
        
    if farmer_state:
        parts.append(f"{farmer_state} state farmers")
    
    if farmer_category:
        parts.append(f"{farmer_category} farmer")
        
    if crop_types:
        parts.append(f"{''.join(crop_types)} cultivation")
        
        
    intent_terms = {
        "list_schemes": "list all schemes benefits eligibility",
        "eligibility_check": "eligibility criteria who can apply requirements",
        "document_requirements": "documents required Aadhaar bank account land records",
        "application_process": "how to apply registration process steps portal",
        "subsidy_query": "subsidy financial support amount benefit payment",
        "scheme_detail": "details objectives features beneficiaries",
    }
    
    
    parts.append(intent_terms.get(intent, "goverment scheme agriculture"))
    
    return " ".join(parts)


def eligibility_analysis_prompt(rag_content : str, farmer_profile : dict,) -> str:
    
    return f"""You are an expert on Indian government agriculture schemes.
 
Analyze the following scheme information and determine eligibility for this farmer.
 
FARMER PROFILE:
{farmer_profile}
 
SCHEME INFORMATION FROM DOCUMENTS:
{rag_content}
 
For each scheme mentioned in the documents, determine:
  1. Is the farmer ELIGIBLE (definitely qualifies based on profile)?
  2. Is it CONDITIONAL (might qualify — some info missing)?
  3. Is the farmer INELIGIBLE (definitely does not qualify)?
 
Output a JSON object:
{{
  "eligible_schemes": [
    {{
      "name": "scheme name",
      "benefit": "what the farmer gets",
      "eligibility_reason": "why this farmer qualifies",
      "documents_required": ["doc1", "doc2"],
      "how_to_apply": "brief steps",
      "official_portal": "URL if mentioned in docs"
    }}
  ],
  "conditional_schemes": [
    {{
      "name": "scheme name",
      "benefit": "what the farmer gets",
      "condition": "what additional info is needed to confirm eligibility"
    }}
  ],
  "ineligible_schemes": [
    {{
      "name": "scheme name",
      "reason": "why this farmer doesn't qualify"
    }}
  ]
}}
 
IMPORTANT:
  - Only include schemes that are explicitly mentioned in the provided documents
  - Do NOT invent or hallucinate scheme names or benefits
  - If state-specific and farmer's state doesn't match, mark ineligible
  - Output JSON only, no explanation
 
Output:"""




def verification_prompt(generated_response : str, rag_sources_text : str,) -> str:
    
    return f"""You are a fact-checker for government scheme information.
 
Review the generated response and check it against the source documents.
 
SOURCE DOCUMENTS:
{rag_sources_text}
 
GENERATED RESPONSE TO CHECK:
{generated_response}
 
Check for:
  1. Any scheme name mentioned in response but NOT in source documents
  2. Any benefit amount/percentage that contradicts the source documents
  3. Any eligibility criteria that contradicts the source documents
  4. Any dates or years that seem outdated (before 2022)
 
Output a JSON object:
{{
  "verification_passed": true or false,
  "hallucination_flags": ["issue1", "issue2"],
  "confidence_score": 0.0 to 1.0,
  "explanation": "brief explanation"
}}
 
confidence_score guide:
  0.9 - 1.0: All claims fully supported by documents
  0.7 - 0.8: Minor issues, mostly supported
  0.4 - 0.6: Some unsupported claims
  0.0 - 0.3: Major hallucinations detected
 
Output (JSON only):"""




def response_generation_prompt(
    farmer_profile : dict,
    eligible_schemes : list,
    conditional_schemes : list,
    rag_sources : list,
    intent : str,
    specific_scheme : Optional[str],
    confidence_score : float,
    history_context : str,
) -> str:
    
    sources_text = "\n".join([
        f"- {s.get('source', 'Unknown')} (Page {s.get('page', '?')})"
        for s in rag_sources
    ]) if rag_sources else "Goverment scheme documents"
    
    confidence_warning = ""
    
    if confidence_score < 0.6:
        confidence_warning = (
            "\n Note: Some information could not be fully verified. "
            "Please confirm details with official sources.\n"
        )
        
    return f"""You are AgriAI, KisanPath's Government Scheme Expert.
 
Generate a helpful, clear response for a farmer in India.
 
FARMER PROFILE:
{farmer_profile}
 
ELIGIBLE SCHEMES:
{eligible_schemes}
 
CONDITIONAL SCHEMES (might qualify):
{conditional_schemes}
 
INTENT: {intent}
SPECIFIC SCHEME ASKED ABOUT: {specific_scheme or "General query"}
{confidence_warning}
 
PREVIOUS CONVERSATION:
{history_context if history_context else "First interaction"}
 
RESPONSE RULES:
  1. Start with a brief direct answer to their question
  2. List eligible schemes with bullet points
  3. For each scheme include: benefit, key eligibility, documents needed, how to apply
  4. Mention conditional schemes with what info is still needed
  5. End with 2-3 relevant follow-up questions the farmer might want to ask
  6. Use simple language — mix Hindi terms where natural (e.g. "kisan", "fasal")
  7. Be encouraging and helpful in tone
  8. Do NOT mention ineligible schemes
  9. Maximum 400 words in response body
 
FORMAT:
  [Your response here]
 
  📋 Sources: {sources_text}
 
  💡 You might also want to ask:
  - [follow-up question 1]
  - [follow-up question 2]
 
Generate the response now:"""
 
 
OUT_OF_SCOPE_RESPONSE = """I'm the Government Scheme Assistant on KisanPath, specialized in helping farmers understand and apply for government agriculture schemes.
 
Your question seems to be about something outside my area of expertise.
 
🌾 I can help you with:
  • Finding schemes you're eligible for
  • PM-KISAN, PMFBY, Soil Health Card, and other central schemes
  • State-specific schemes (KALIA, Rythu Bandhu, etc.)
  • Documents required to apply
  • Application process and portals
  • Subsidies for seeds, fertilizers, irrigation, equipment
 
For other farming questions (crop advice, pest control, weather, prices), please use the **AgriAI Chatbot** available in your KisanPath dashboard.
 
What government scheme information can I help you with? 🏛️"""



def error_response(error_type : str) -> str:
    
    messages = {
        "rag_unavailable": (
            "I'm having trouble accessing the scheme database right now. "
            "Please try again in a moment, or contact your nearest "
            "Krishi Vigyan Kendra (KVK) for immediate assistance."
        ),
        "llm_unavailable": (
            "The AI service is temporarily unavailable. "
            "Please try again in a few minutes."
        ),
        "db_unavailable": (
            "I couldn't load your profile right now, but I can still help with general scheme information. "
            "Please tell me your state and land size so I can give you personalized recommendations."
        ),
        "general": (
            "I encountered an issue while processing your request. "
            "Please try rephrasing your question, or contact KVK for assistance."
        ),
    }
    return messages.get(error_type, messages["general"])