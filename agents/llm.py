import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm():
    """
    Initialize and return the configured Gemini Chat Model.
    Raises ValueError if GEMINI_API_KEY is not configured.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")
        
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    
    # LangChain's ChatGoogleGenerativeAI natively supports tool calling
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        disable_streaming=True
    )
    
    return llm
