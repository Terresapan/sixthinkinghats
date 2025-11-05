import os
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import streamlit as st

# Import new modules
from services import SearchOrchestrator, SearchAPIFactory
from graph import create_parallel_processor, process_thinking_hats_query

os.environ["GROQ_API_KEY"] = st.secrets["general"]["GROQ_API_KEY"]
os.environ["GEMINI_API_KEY"] = st.secrets["general"]["GEMINI_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["general"]["OPENAI_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]["API_KEY"]
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "Six_Thinkning_Hats"

# Set up environment for Tavily search if available
if "general" in st.secrets and "TAVILY_API_KEY" in st.secrets["general"]:
    os.environ["TAVILY_API_KEY"] = st.secrets["general"]["TAVILY_API_KEY"]

# Define state
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]

# Create the LLM
llm_groq = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0,
    max_tokens=2000,
    timeout=None,
    max_retries=2,
)

llm_genai = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.environ["GEMINI_API_KEY"],
    temperature=0,
    max_tokens=2000,
    timeout=None,
    max_retries=2,
)

llm_openai = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ["OPENAI_API_KEY"],
    temperature=0,
    timeout=None,
    # max_retries=2,
)

# Initialize parallel processor (this will be used in the new architecture)
_parallel_processor = None

def get_parallel_processor():
    """Get or create the parallel processor instance."""
    global _parallel_processor
    if _parallel_processor is None:
        try:
            _parallel_processor = create_parallel_processor(
                llm_openai, 
                search_enabled=True
            )
        except Exception as e:
            print(f"Warning: Could not initialize parallel processor: {e}")
            _parallel_processor = None
    return _parallel_processor

# Legacy functions (kept for compatibility)
def create_node(state, system_prompt):
    human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
    system_message = [SystemMessage(content=system_prompt)]
    messages = system_message + human_messages + ai_messages
    message = llm_openai.invoke(messages)
    return {"messages": [message]}

blue = lambda state: create_node(state, "You are Blue Hat. You Represents process and organization. You are tasked with kicking off the discussion and setting the goal and scope. Please note the discussion order after you is: White Hat, Red Hat, Yellow Hat, Black Hat, Green Hat, and Blue Hat again for the final summary. Limit your response within 200 words.")

white = lambda state: create_node(state, "You are White Hat. You Represents neutrality and facts. You are tasked with providing the data and information available, without emotional attachment or personal opinions. Limit your response within 200 words.")

red = lambda state: create_node(state, "You are Red Hat. You Represents emotions and feelings. You are tasked with expressing your emotions and intuition, without justification or explanation. Limit your response within 200 words.")

yellow = lambda state: create_node(state, "You are Yellow Hat. You Represents optimism and positive thinking. You are tasked with providing a positive outlook, focusing on the benefits, advantages, and opportunities of a particular idea or decision. Limit your response within 200 words.") 

black = lambda state: create_node(state, "You are Black Hat. You Represents skepticism and skepticism. You are tasked with providing the potential risks, drawbacks, and limitations of a particular idea or decision. Limit your response within 200 words.")

green = lambda state: create_node(state, "You are Green Hat. You Represents creativity and new ideas. You are tasked with generating innovative solutions, thinking outside the box, and exploring new possibilities. Limit your response within 200 words.")

summary = lambda state: create_node(state, "You are Blue Hat. You Represents process and organization. You are tasked with summarizing the discussion. Please make sure to answer uesr's question explicetly and clearly. Limit your response within 200 words.")

# Create the graph (legacy)
builder = StateGraph(GraphState)

# Add nodes to the graph
builder.add_node("blue", blue)
builder.add_node("white", white)
builder.add_node("red", red)
builder.add_node("yellow", yellow)
builder.add_node("black", black)
builder.add_node("green", green)
builder.add_node("summary", summary)

# Set entry point and edges
builder.add_edge(START, "blue")
builder.add_edge("blue", "white")
builder.add_edge("white", "red")
builder.add_edge("red", "yellow")
builder.add_edge("yellow", "black")
builder.add_edge("black", "green")
builder.add_edge("green", "summary")
builder.add_edge("summary", END)

# Compile and run the builder
graph = builder.compile()

# Draw the graph
try:
    graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")
except Exception:
    pass

# NEW: Enhanced processing function with search and parallel execution
async def process_query_with_search(user_query: str, search_enabled: bool = True) -> dict:
    """
    Process a query using the new parallel system with search integration.
    
    Args:
        user_query: The user's query
        search_enabled: Whether to enable web search
        
    Returns:
        Dictionary containing all agent responses and metadata
    """
    processor = get_parallel_processor()
    
    if processor is None:
        # Fallback to legacy system
        return await process_legacy_query(user_query)
    
    try:
        # Use the new parallel processing system
        results = await process_thinking_hats_query(
            llm_openai, 
            user_query, 
            search_enabled=search_enabled
        )
        return results
    except Exception as e:
        print(f"Error in parallel processing: {e}")
        # Fallback to legacy system
        return await process_legacy_query(user_query)

# Legacy processing function as fallback
async def process_legacy_query(user_query: str) -> dict:
    """Fallback to the legacy sequential processing."""
    try:
        response = graph.invoke({"messages": [HumanMessage(content=user_query)]})
        ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
        
        return {
            "user_query": user_query,
            "results": {
                "white_hat": {"response": ai_messages[-6].content, "search_used": False},
                "red_hat": {"response": ai_messages[-5].content, "search_used": False},
                "yellow_hat": {"response": ai_messages[-4].content, "search_used": False},
                "black_hat": {"response": ai_messages[-3].content, "search_used": False},
                "green_hat": {"response": ai_messages[-2].content, "search_used": False},
                "blue_hat": {"response": ai_messages[-1].content, "search_used": False}
            },
            "statistics": {
                "total_agents": 6,
                "successful_agents": 6,
                "searches_performed": 0,
                "success_rate": "100.0%"
            },
            "processing_mode": "legacy"
        }
    except Exception as e:
        return {
            "user_query": user_query,
            "error": str(e),
            "results": {},
            "statistics": {"total_agents": 0, "successful_agents": 0},
            "processing_mode": "legacy_error"
        }

# Main enhanced loop
async def main_loop():
    """Enhanced main loop with search and parallel processing."""
    print("🚀 Enhanced Six Thinking Hats with Web Search")
    print("Commands:")
    print("  'search on'  - Enable web search")
    print("  'search off' - Disable web search") 
    print("  'stats'      - Show processing statistics")
    print("  'quit'       - Exit")
    print("-" * 50)
    
    search_enabled = True
    
    while True:
        user_input = input(">> ")
        
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        elif user_input.lower() == "search on":
            search_enabled = True
            print("✅ Web search enabled")
            continue
        
        elif user_input.lower() == "search off":
            search_enabled = False
            print("❌ Web search disabled")
            continue
        
        elif user_input.lower() == "stats":
            processor = get_parallel_processor()
            if processor:
                stats = processor.get_processing_statistics()
                print("📊 Processing Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            else:
                print("📊 No statistics available")
            continue
        
        print(f"\n🔍 Processing with {'search enabled' if search_enabled else 'search disabled'}...")
        
        try:
            results = await process_query_with_search(user_input, search_enabled)
            
            # Display results
            if "error" in results:
                print(f"❌ Error: {results['error']}")
                continue
            
            print("\n" + "="*60)
            print("🎩 THINKING HATS ANALYSIS RESULTS")
            print("="*60)
            
            hat_names = {
                "white_hat": "🔍 White Hat (Facts)",
                "red_hat": "❤️ Red Hat (Feelings)", 
                "yellow_hat": "☀️ Yellow Hat (Optimism)",
                "black_hat": "⚫ Black Hat (Risks)",
                "green_hat": "🌱 Green Hat (Creativity)",
                "blue_hat": "🔵 Blue Hat (Summary)"
            }
            
            for hat_key, hat_name in hat_names.items():
                if hat_key in results["results"]:
                    response_data = results["results"][hat_key]
                    response = response_data.get("response", "No response")
                    search_used = response_data.get("search_used", False)
                    
                    print(f"\n{hat_name}")
                    print("-" * 40)
                    print(response)
                    if search_used:
                        print("  📱 [Used web search]")
            
            # Show processing statistics
            if "statistics" in results:
                stats = results["statistics"]
                print(f"\n📊 Statistics:")
                print(f"  Agents processed: {stats.get('successful_agents', 0)}/{stats.get('total_agents', 0)}")
                print(f"  Search queries: {stats.get('searches_performed', 0)}")
                print(f"  Success rate: {stats.get('success_rate', 'N/A')}")
                
                if "processing_time" in results:
                    print(f"  Processing time: {results['processing_time']:.2f}s")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ Processing error: {str(e)}")

# Enhanced synchronous interface
def sync_main_loop():
    """Synchronous wrapper for the enhanced main loop."""
    asyncio.run(main_loop())

# Run the enhanced main loop
if __name__ == "__main__":
    sync_main_loop()
