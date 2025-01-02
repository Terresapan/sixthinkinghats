import streamlit as st
from main import graph
from langchain_core.messages import AIMessage, HumanMessage

def generate_message(user_input, messages_container):
    # Show processing state
    with st.status("🤖 The AI team is processing your request...", expanded=True) as status:
        # Get responses from the AI team
        status.update(label="🔄 Getting responses from the team...", state="running")
        response = graph.invoke({"messages": [HumanMessage(content=user_input)]})
        ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
        
        # Store the conversation
        current_conversation = {
            "user": user_input,
            "blue": ai_messages[-7].content,
            "white": ai_messages[-6].content,
            "red": ai_messages[-5].content,
            "yellow": ai_messages[-4].content,
            "black": ai_messages[-3].content,
            "green": ai_messages[-2].content,
            "summary": ai_messages[-1].content,
        }
        st.session_state.conversation.append(current_conversation)
        
        # Display user message
        messages_container.chat_message("user", avatar="img/user.png").write(user_input)
        
        # Display team responses
        status.update(label="💬 Displaying team responses...", state="running")
        
        roles = [
            ("blue", "Blue Hat", "img/blue.png"),
            ("white", "White Hat", "img/white.png"),
            ("red", "Red Hat", "img/red.png"),
            ("yellow", "Yellow Hat", "img/yellow.png"),
            ("black", "Black Hat", "img/black.png"),
            ("green", "Green Hat", "img/green.png"),
            ("summary", "Blue Hat", "img/blue.png")
        ]
        
        for role, title, avatar in roles:
            messages_container.chat_message("ai", avatar=avatar).write(
                f"**{title}:** \n{current_conversation[role]}"
            )
            
        status.update(label="✅ Response complete!", state="complete")

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
        messages.chat_message("user", avatar="img/user.png").write(entry['user'])
        
        for role, title, avatar in [
            ("blue", "Blue Hat", "img/blue.png"),
            ("white", "White Hat", "img/white.png"),
            ("red", "Red Hat", "img/red.png"),
            ("yellow", "Yellow Hat", "img/yellow.png"),
            ("black", "Black Hat", "img/black.png"),
            ("green", "Green Hat", "img/green.png"),
            ("summary", "Summary", "img/blue.png"),
        ]:
            messages.chat_message("ai", avatar=avatar).write(f"**{title}:** \n{entry[role]}")
       
    # Chatbot UI
    if prompt := st.chat_input("Enter your question...", key="prompt"):
        generate_message(prompt, messages)

if __name__ == "__main__":
    main()