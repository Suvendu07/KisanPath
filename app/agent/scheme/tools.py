import json
import logging
from typing import Optional
from sqlalchemy.orm import Session



logger = logging.getLogger(__name__)



def get_farmer_profile_from_db(user_id : int, db : Session) -> dict:
    
    """
    Loads farmer profile from the existing farmers + users tables.
    Returns a dict of known fields. Empty dict if not a farmer or DB error.
 
    This is called by input_processor to pre-fill the state
    so the agent doesn't have to ask for basic info already in DB.
    """
    
    try:
        from app.models.farmer_model import Farmer
        from app.models.user_model import User

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        base = {
            "farmer_name" : user.full_name,
            "farmer_state" : user.state,
            "farmer_district" : user.city,
            "has_bank_account" : None,
            "has_aadhar" : None,
        }
        
        
        if user.role.value != "farmer":
            return base
        
        farmer = db.query(Farmer).filter(Farmer.user_id == user_id).first()
        if not farmer:
            return base
        
        base.update({
            "land_size_acres" : farmer.farm_size_acres,
            "farmer_state" : user.state or (
                farmer.farm_location.split(",")[-1].strip()
                if farmer.farm_location else None
            ),
            "kisan_id" : farmer.kisan_id,
        })
        
        if farmer.farm_size_acres:
            if farmer.farm_size_acres < 1.0:
                base["farmer_category"] = "marginal"
                
            elif farmer.farm_size_acres <= 2.0:
                base["farmer_category"] = "small"
                
            else:
                base["farmer_category"] = "large"
                
        return {k:v for k, v in base.items() if v is not None}
    
    except Exception as e:
        logger.error(f"get_farmer_profile_from_db failed for user {user_id} : {e}")
        
        
        
        
def faiss_retrieve_schemes(enriched_query : str, top_k : int = 6,) -> tuple[list, list]:
    
    """
    Retrieves relevant document chunks from FAISS vector store.
    Returns (chunks_text_list, sources_list).
 
    Uses the existing rag_service.load_vector_store() —
    no duplication of FAISS initialization.
    """
    
    try:
        from app.services.rag_service import load_vector_store
        
        vector_store = load_vector_store()
        retriever = vector_store.as_retriever(
            search_type = "similarity",
            search_kwargs = {"k" : top_k},
        )
        
        docs = retriever.invoke(enriched_query)
        chunks = [doc.page_content for doc in docs]
        sources = []
        seen = set()
        
        
        for doc in docs:
            meta = doc.metadata
            src_key = f"{meta.get('source', 'unknown')} : {meta.get('page',0)}"
            
            if src_key not in seen:
                seen.add(src_key)
                
                import os

                sources.append({
                    "source" : os.path.basename(meta.get("source" , "unknown")),
                    "page" : meta.get("page", 0) + 1,
                    "excerpt" : doc.page_content[:200],
                })
                
                
        return chunks, sources
    
    except Exception as e:
        logger.error(f"faiss_retrieve_schemes failed : {e}")
        return [], []