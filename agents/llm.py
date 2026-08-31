import os
from dotenv import load_dotenv
from langchain_core.messages import AIMessage


class DemoLLM:
    """
    Deterministic LLM fallback for demo mode.
    Only provides minimal structured responses where the LLM is required.
    All agent execution uses real deterministic business tools.
    """
    
    def __init__(self):
        self.demo_mode = True
    
    def with_structured_output(self, output_schema):
        """Return a structured output wrapper for LLM-required decisions."""
        return DemoStructuredLLM(output_schema)
    
    def invoke(self, messages):
        """
        Generic LLM invocation for synthesis.
        Returns minimal deterministic response without claiming findings.
        """
        response_text = """[DEMO MODE — deterministic LLM fallback]

This is a synthesis of the verified findings from the evidence verifier and decision agent.
The actual analysis was performed by the specialist agents using deterministic business tools on real data."""
        
        return AIMessage(content=response_text)
    
    def bind_tools(self, tools):
        """Return self for tool binding compatibility."""
        return self


class DemoStructuredLLM:
    """
    Structured output wrapper for demo mode.
    Provides minimal deterministic routing/decisions only.
    """
    
    def __init__(self, output_schema):
        self.output_schema = output_schema
    
    def invoke(self, messages):
        """
        Return minimal structured output for LLM-required decisions.
        Orchestrator routing and Decision Agent guidance only.
        """
        schema_name = self.output_schema.__name__ if hasattr(self.output_schema, '__name__') else str(self.output_schema)
        
        if 'InvestigationPlan' in schema_name:
            # Orchestrator: simple routing based on question keywords
                       # Orchestrator: simple routing based on question keywords
            question_text = ""
            if isinstance(messages, list):
                fallback_text = ""
                for msg in messages:
                    if not hasattr(msg, 'content'):
                        continue
                    msg_type = getattr(msg, 'type', None)
                    if not fallback_text:
                        fallback_text = msg.content.lower()
                    # Prefer the actual human/user message over system/other messages
                    if msg_type == 'human' or msg.__class__.__name__ == 'HumanMessage':
                        question_text = msg.content.lower()
                if not question_text:
                    question_text = fallback_text
            
            # Simple keyword-based routing
            agents = []
            if any(word in question_text for word in ["revenue", "profit", "sales", "margin"]):
                agents.append("sales")
            if any(word in question_text for word in ["stockout", "inventory", "stock", "available"]):
                agents.append("inventory")
            if any(word in question_text for word in ["customer", "churn", "customer behavior"]):
                agents.append("customer")
            
            if not agents:
                agents = ["sales"]  # Default fallback
            
            return self.output_schema(
                selected_agents=agents,
                reason="[DEMO MODE] Routing determined by keyword matching on the user question."
            )
        
        elif 'DecisionReport' in schema_name:
            # Decision Agent: minimal guidance based on verification results
            return self.output_schema(
                primary_driver="[DEMO MODE] Decision based on verified evidence from deterministic tools.",
                confidence=0.50,
                recommended_actions=["Review the verified findings from the evidence verifier."]
            )
        
        return self.output_schema()


def get_llm():
    """
    Initialize and return the configured LLM.
    
    Demo mode (DEMO_MODE=true/1/yes):
      - Returns DemoLLM instance for deterministic routing/decisions
      - All agent nodes execute with real deterministic business tools
      - No Gemini API calls made
    
    Normal mode (DEMO_MODE unset/false):
      - Uses real Gemini API with GEMINI_API_KEY
      - Full LLM capability for all agents
    
    Raises ValueError if GEMINI_API_KEY is not set and DEMO_MODE is not enabled.
    """
    load_dotenv()
    
    # Check for demo mode FIRST, before any other imports
    demo_mode = os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes")
    if demo_mode:
        return DemoLLM()
    
    # Normal mode: Use real Gemini API
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured. Set GEMINI_API_KEY or use DEMO_MODE=true.")
        
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    
    # LangChain's ChatGoogleGenerativeAI with Gemini 3.6 Flash
    # disable_streaming=True and max_tokens=8192 prevent prefilling errors
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        disable_streaming=True,
        max_tokens=8192
    )
    
    return llm
