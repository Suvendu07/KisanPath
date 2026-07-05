from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_classic.prompts import PromptTemplate
from langchain_classic.chains.conversation.base import ConversationChain


from app.config import settings
from app.schemas.ai import ChatRequest, ChatResponse, ChatMessage
# from dotenv import load_dotenv

# load_dotenv()



AGRI_SYSTEM_PROMPT = """You are AgriAI, an expert agricultural assistant built into KisanPath —
a digital platform connecting Indian farmers, vendors, and buyers.
 
Your expertise:
- Crop cultivation techniques (Kharif, Rabi, Zaid seasons)
- Soil health, NPK management, pH correction
- Pest and disease identification and treatment
- Irrigation scheduling and water management
- Government schemes: PM-KISAN, Soil Health Card, PMFBY (crop insurance)
- Market prices, mandi rates, selling strategies
- Organic farming and modern agri-tech
 
Rules:
- Always respond in the language the farmer writes in (Hindi/English/mix)
- Keep answers practical and actionable — farmers need solutions, not lectures
- For disease/pest issues always end with: Immediate action + Preventive measure
- For unrelated questions say: "Main sirf kheti-baadi ke baare mein madad kar sakta hoon!"
- Always end farming advice with one short "Pro Tip 🌱:"
 
Current conversation:
{history}
 
Farmer: {input}
AgriAI:"""



def get_llm() -> ChatGoogleGenerativeAI:
    
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured in .env")
    
    
    return ChatGoogleGenerativeAI(
        model = "gemini-2.5-flash",
        google_api_key = settings.GEMINI_API_KEY,
        temperature = 0.7,
        max_tokens = 1024,
    )
    
    

def build_chain(history : list[ChatMessage]) -> ConversationChain:
    
    llm = get_llm()
    
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=AGRI_SYSTEM_PROMPT,
    )
    
    
    memory = ConversationBufferWindowMemory(
        k = settings.CHAT_MEMORY_WINDOW,
        human_prefix= "Farmer",
        ai_prefix="AgriAI",
        return_messages=False,
    )
    
    
    for msg in history:
        if msg.role == "human":
            memory.chat_memory.add_user_message(msg.content)
            
        elif msg.role == "ai":
            memory.chat_memory.add_ai_message(msg.content)
            
    
    chain = ConversationChain(
        llm = llm,
        memory=memory,
        prompt=prompt,
        verbose=False,
    )
    
    
    return chain, memory



def chat_with_agri_ai(payload : ChatRequest) -> ChatResponse:
    
    try:
        chain, memory = build_chain(payload.history)
        reply = chain.predict(input=payload.message)
        reply = reply.strip()
        
    
    except ValueError as e:
        raise ValueError(str(e))
    
    except Exception as e:
        raise RuntimeError(f"Langchain error: {str(e)}")
    
    
    updated_history = list(payload.history) + [
        ChatMessage(role = "human", content=payload.message),
        ChatMessage(role = "ai", content=reply),
    ]
    
    
    max_message = settings.CHAT_MEMORY_WINDOW * 2
    if len(updated_history) > max_message:
        updated_history = updated_history[-max_message:]
        
    
    return ChatResponse(
        reply = reply,
        session_id= payload.session_id,
        history = updated_history,
    )