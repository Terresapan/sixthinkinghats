import os
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import streamlit as st

os.environ["GROQ_API_KEY"] = st.secrets["general"]["GROQ_API_KEY"]
os.environ["GEMINI_API_KEY"] = st.secrets["general"]["GEMINI_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["general"]["OPENAI_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]["API_KEY"]
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "Six_Thinkning_Hats"

# Define state
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]

# Create the graph
builder = StateGraph(GraphState)

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
    model="gemini-2.0-flash-exp",
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
    max_tokens=2000,
    timeout=None,
    # max_retries=2,
)

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

# Create a main loop
def main_loop():
        # Run the chatbot
    while True:
        user_input = input(">> ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        response = graph.invoke({"messages": [HumanMessage(content=user_input)]})
        print("Blue Hat: ", response["messages"][-7].content)
        print("White Hat: ", response["messages"][-6].content)
        print("Red Hat: ", response["messages"][-5].content)
        print("Yellow Hat: ", response["messages"][-4].content)
        print("Black Hat: ", response["messages"][-3].content)
        print("Green Hat: ", response["messages"][-2].content)
        print("Summary: ", response["messages"][-1].content)

# Run the main loop
if __name__ == "__main__":
    main_loop()