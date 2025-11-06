import streamlit as st
import asyncio
import toml
from langchain_openai import ChatOpenAI

# Import phased workflow graph
from graph.phased_workflow_graph import PhasedWorkflowGraph
from services.search_apis import TavilySearchAPI


def load_secrets():
    """Load API keys from .streamlit/secrets.toml."""
    secrets_file = ".streamlit/secrets.toml"
    try:
        with open(secrets_file, "r") as f:
            secrets = toml.load(f)

        os_environ = {}
        if "general" in secrets:
            if "OPENAI_API_KEY" in secrets["general"]:
                os_environ["OPENAI_API_KEY"] = secrets["general"]["OPENAI_API_KEY"]
            if "TAVILY_API_KEY" in secrets["general"]:
                os_environ["TAVILY_API_KEY"] = secrets["general"]["TAVILY_API_KEY"]

        if "LANGCHAIN_API_KEY" in secrets:
            os_environ["LANGCHAIN_API_KEY"] = secrets["LANGCHAIN_API_KEY"]["API_KEY"]

        return os_environ
    except Exception as e:
        st.error(f"Could not load secrets: {e}")
        return {}


def get_llm():
    """Create and configure the LLM."""
    import os

    secrets = load_secrets()

    if "OPENAI_API_KEY" in secrets:
        os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]

    # Also set TAVILY_API_KEY for search
    if "TAVILY_API_KEY" in secrets:
        os.environ["TAVILY_API_KEY"] = secrets["TAVILY_API_KEY"]

    if "LANGCHAIN_API_KEY" in secrets:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_PROJECT"] = "Six_Thinkning_Hats"
        os.environ["LANGCHAIN_API_KEY"] = secrets["LANGCHAIN_API_KEY"]

    return ChatOpenAI(
        model="gpt-5-mini",
        api_key=secrets.get("OPENAI_API_KEY"),
        temperature=0,
        timeout=None,
    )


async def generate_message_async(user_input, messages_container, llm):
    """Generate message using phased workflow graph."""

    # Show processing state
    with st.status("🤖 The AI team is processing your request...", expanded=True) as status:
        # Initialize the phased workflow graph
        status.update(label="🔄 Initializing phased workflow...", state="running")

        try:
            # Create search API
            search_api = TavilySearchAPI()

            # Create the phased workflow
            workflow = PhasedWorkflowGraph(
                llm=llm,
                search_api=search_api,
                max_searches_per_query=4
            )

            # Execute the workflow
            status.update(label="🔄 Executing phased workflow...", state="running")

            results = workflow.invoke(user_input)

            # Store the conversation
            current_conversation = {
                "user": user_input,
                "white": results.get("white_response", "No response"),
                "red": results.get("red_response", "No response"),
                "yellow": results.get("yellow_response", "No response"),
                "black": results.get("black_response", "No response"),
                "green": results.get("green_response", "No response"),
                "summary": results.get("blue_response", "No response"),
                "statistics": results.get("processing_stats", {}),
                "errors": results.get("errors", []),
                "processing_mode": "phased_workflow",
            }

            st.session_state.conversation.append(current_conversation)

            # Display user message
            messages_container.chat_message("user", avatar="img/user.png").write(user_input)

            # Display team responses with phase indicators
            status.update(label="💬 Displaying team responses...", state="running")

            # Phase 1: Parallel hats
            status.update(label="📋 Phase 1: White, Red, Yellow, Black (Parallel)", state="running")

            parallel_roles = [
                ("white", "White Hat (Facts)", "img/white.png"),
                ("red", "Red Hat (Feelings)", "img/red.png"),
                ("yellow", "Yellow Hat (Optimism)", "img/yellow.png"),
                ("black", "Black Hat (Risks)", "img/black.png"),
            ]

            for role, title, avatar in parallel_roles:
                response_text = current_conversation[role]
                # Check if search was used for this hat
                search_used = current_conversation.get("statistics", {}).get(role, {}).get("search_used", False)
                search_indicator = " 📱" if search_used else ""

                messages_container.chat_message("ai", avatar=avatar).write(
                    f"**{title}{search_indicator} (Phase 1):** \n{response_text}"
                )

            # Phase 2: Green Hat
            status.update(label="🌱 Phase 2: Green Hat (Creative)", state="running")
            green_response = current_conversation["green"]
            green_search_used = current_conversation.get("statistics", {}).get("green_hat", {}).get("search_used", False)
            green_indicator = " 📱" if green_search_used else ""
            messages_container.chat_message("ai", avatar="img/green.png").write(
                f"**Green Hat (Creativity){green_indicator} (Phase 2):** \n{green_response}"
            )

            # Phase 3: Blue Hat
            status.update(label="🔵 Phase 3: Blue Hat (Summary)", state="running")
            summary_response = current_conversation["summary"]
            messages_container.chat_message("ai", avatar="img/blue.png").write(
                f"**Blue Hat (Summary) (Phase 3):** \n{summary_response}"
            )

            # Display processing statistics if available
            if "statistics" in current_conversation:
                stats = current_conversation["statistics"]
                messages_container.chat_message("ai", avatar="📊").write(
                    f"**Processing Statistics:**\n"
                    f"- Phases completed: {', '.join(stats.get('overall', {}).get('phases_completed', []))}\n"
                    f"- Total execution time: {stats.get('overall', {}).get('total_execution_time', 0):.2f}s\n"
                    f"- Errors encountered: {stats.get('overall', {}).get('total_errors', 0)}\n"
                    f"- Processing mode: {current_conversation.get('processing_mode', 'N/A')}"
                )

            # Display any errors
            errors = current_conversation.get("errors", [])
            if errors:
                error_msg = "\n".join(errors)
                messages_container.chat_message("ai", avatar="⚠️").write(
                    f"**Errors Encountered:**\n{error_msg}"
                )

            status.update(label="✅ Response complete!", state="complete")

        except Exception as e:
            status.update(label="❌ Error occurred", state="error")
            st.error(f"Processing error: {str(e)}")
            # Add error to conversation
            st.session_state.conversation.append(
                {
                    "user": user_input,
                    "error": str(e),
                    "processing_mode": "error",
                }
            )


def generate_message(user_input, messages_container, llm):
    """Wrapper to call async function from Streamlit."""
    asyncio.run(generate_message_async(user_input, messages_container, llm))


def main():
    # Define constants
    height = 1000
    title = "Six Thinking Hats Discussion App 🧢"

    # Session: Initialize conversation history
    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    # Set page title and icon
    st.set_page_config(page_title=title, page_icon="🧢")
    st.header(title)

    # Create a container for the chat messages
    messages = st.container(border=True, height=height)

    # Display previous conversation
    for entry in st.session_state.conversation:
        messages.chat_message("user", avatar="img/user.png").write(entry["user"])

        # Display parallel hats with phase indicators
        for role, title, avatar in [
            ("white", "🔍 White Hat (Facts) (Phase 1)", "img/white.png"),
            ("red", "❤️ Red Hat (Feelings) (Phase 1)", "img/red.png"),
            ("yellow", "☀️ Yellow Hat (Optimism) (Phase 1)", "img/yellow.png"),
            ("black", "⚫ Black Hat (Risks) (Phase 1)", "img/black.png"),
        ]:
            if role in entry:
                messages.chat_message("ai", avatar=avatar).write(f"**{title}:** \n{entry[role]}")

        # Display Green Hat
        if "green" in entry:
            messages.chat_message("ai", avatar="img/green.png").write(
                f"**🌱 Green Hat (Creativity) (Phase 2):** \n{entry['green']}"
            )

        # Display Blue Hat
        if "summary" in entry:
            messages.chat_message("ai", avatar="img/blue.png").write(
                f"**🔵 Blue Hat (Summary) (Phase 3):** \n{entry['summary']}"
            )

    # Get LLM instance
    llm = get_llm()

    # Chatbot UI
    if prompt := st.chat_input("Enter your question...", key="prompt"):
        generate_message(prompt, messages, llm)


if __name__ == "__main__":
    main()
