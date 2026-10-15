import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="SandX-OmniNode AI",
    page_icon="🤖",
    layout="wide"
)

# Initialize Gemini API securely using Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ GEMINI_API_KEY not found in Streamlit Secrets! Please add it in your app settings.")
    st.stop()

# Initialize model
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config
)

# App Header
st.title("🤖 SandX-OmniNode AI Assistant")
st.markdown("Aapka apna advanced AI assistant, ab Streamlit Cloud par live!")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Yahan apna sawal likhiye..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⏳ Soch raha hoon...")
        
        try:
            # Format chat history for Gemini
            chat_history = [
                {"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]}
                for m in st.session_state.messages[:-1]
            ]
            
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(prompt)
            
            ai_response = response.text
            message_placeholder.markdown(ai_response)
            
            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            error_msg = f"⚠️ **Execution Error:** {str(e)}"
            message_placeholder.markdown(error_msg)