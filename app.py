import os
import json
import time
import streamlit as st
from PIL import Image
import pypdf
import google.generativeai as genai
from auth import register_user, verify_user

# Page Config
st.set_page_config(page_title="SandX-OmniNode AI", page_icon="⚡", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization for Authentication
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- SECURE LOGIN / SIGNUP SCREEN ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.3, 1])
    
    with col2:
        st.markdown("## ⚡ SandX-OmniNode AI Portal")
        st.caption("Secure Multi-User Access Gateway")
        st.write("---")
        
        auth_mode = st.radio("Choose Mode", ["Login", "Sign Up (Register)"], horizontal=True)
        
        email_input = st.text_input("📧 Email Address", key="auth_email")
        pass_input = st.text_input("🔑 Password", type="password", key="auth_pass")
        
        if auth_mode == "Sign Up (Register)":
            if st.button("📝 Register Account", use_container_width=True):
                success, msg = register_user(email_input, pass_input)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
        else:
            if st.button("🚀 Secure Login", use_container_width=True):
                success, msg = verify_user(email_input, pass_input)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input.strip().lower()
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error(msg)
        
        st.write("---")
        st.info("💡 **Tip:** Pehle 'Sign Up' karke naya account banayein, phir 'Login' karein.")
    
    st.stop()


# --- MAIN AI APP (After Login) ---
HISTORY_FILE = f"chat_history_{st.session_state.user_email.replace('@', '_').replace('.', '_')}.json"

def load_all_chats():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_all_chats(chats_data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(chats_data, f, ensure_ascii=False, indent=2)

if "chats" not in st.session_state:
    st.session_state.chats = load_all_chats()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "Session 1"

if st.session_state.current_chat_id not in st.session_state.chats:
    st.session_state.chats[st.session_state.current_chat_id] = []

# Sidebar Design
with st.sidebar:
    st.title("⚡ SandX Hub")
    st.caption(f"User: {st.session_state.user_email}")
    st.write("---")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = f"Session {len(st.session_state.chats) + 1}"
        st.session_state.current_chat_id = new_id
        st.session_state.chats[new_id] = []
        save_all_chats(st.session_state.chats)
        st.rerun()

    st.write("---")
    st.markdown("### 📜 Saved Conversations")
    
    chat_ids = list(st.session_state.chats.keys())
    chat_ids.reverse()
    
    for cid in chat_ids:
        messages = st.session_state.chats[cid]
        first_msg = messages[0]["content"] if messages else "Empty Chat"
        title_snippet = (first_msg[:20] + "..") if len(first_msg) > 20 else first_msg
        
        button_label = f"💬 {cid}: {title_snippet}"
        if cid == st.session_state.current_chat_id:
            button_label = f"▶️ {cid}: {title_snippet}"
            
        if st.button(button_label, key=f"btn_{cid}", use_container_width=True):
            st.session_state.current_chat_id = cid
            st.rerun()

    st.write("---")
    
    with st.expander("🛠️ Active Capabilities"):
        st.markdown("""
        * 🤖 **Gemini Auto-Resilient Engine**
        * 🖼️ **Gemini Fast Vision**
        * 📁 **PDF Notes RAG Parsing**
        """)

    with st.expander("⚙️ System Health"):
        st.markdown("""
        * **Engine:** Rate-Limit Protected 🛡️
        * **Status:** Operational 🟢
        """)
        
    st.write("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()
        
    st.caption("Developed by Sandeep | 2026")

# Header Area
st.title("⚡ SandX-OmniNode AI")
st.write("---")

# API Key Setup
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error("⚠️ GEMINI_API_KEY not found in Streamlit Secrets!")
    st.stop()

# Helper function to generate content with automatic retries and model fallbacks
def generate_safe_response(contents, message_placeholder):
    models_to_try = ['gemini-3.8-flash', 'gemini-1.5-flash', 'gemini-pro']
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(contents, stream=True)
            
            full_text = ""
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    message_placeholder.markdown(full_text + "▌")
            
            message_placeholder.markdown(full_text)
            return full_text
            
        except Exception as err:
            err_msg = str(err)
            if "429" in err_msg or "quota" in err_msg.lower():
                message_placeholder.markdown("⏳ *API Rate Limit hit. Waiting 3 seconds before auto-retrying...*")
                time.sleep(3)
                continue
            elif "404" in err_msg or "not found" in err_msg.lower():
                continue
            else:
                raise err
                
    # Final retry with gemini-3.8-flash after brief pause
    time.sleep(4)
    model = genai.GenerativeModel('gemini-3.8-flash')
    response = model.generate_content(contents, stream=False)
    message_placeholder.markdown(response.text)
    return response.text

# Display active chat history
current_messages = st.session_state.chats[st.session_state.current_chat_id]
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Layout: Chat Input + Attachments
col1, col2, col3 = st.columns([0.70, 0.15, 0.15])

with col2:
    uploaded_image = st.file_uploader("🖼️ Image", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

with col3:
    uploaded_pdf = st.file_uploader("📁 PDF Notes", type=["pdf"], label_visibility="collapsed")

with col1:
    user_query = st.chat_input("SandX-Node se kuch bhi puchein ya image/notes upload karein...")

# File Processing Logic
file_attached = False
file_obj = None
file_type = ""
file_name = ""
pdf_extracted_text = ""

if uploaded_image is not None:
    try:
        file_obj = Image.open(uploaded_image)
        file_attached = True
        file_type = "image"
        file_name = uploaded_image.name
    except Exception as e:
        st.error(f"Image read error: {str(e)}")
elif uploaded_pdf is not None:
    try:
        reader = pypdf.PdfReader(uploaded_pdf)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                pdf_extracted_text += extracted + "\n"
        file_attached = True
        file_type = "pdf"
        file_name = uploaded_pdf.name
    except Exception as e:
        st.error(f"PDF read error: {str(e)}")

# Main Trigger
if user_query:
    display_content = f"📁 *[Attached {file_type.upper()}: {file_name}]* \n\n {user_query}" if file_attached else user_query

    current_messages.append({"role": "user", "content": display_content})
    st.session_state.chats[st.session_state.current_chat_id] = current_messages
    save_all_chats(st.session_state.chats)

    with st.chat_message("user"):
        st.markdown(display_content)
        if file_attached and file_type == "image" and file_obj:
            st.image(file_obj, caption="Uploaded Image", width=300)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            system_instruction = """
            You are SandX-OmniNode AI created by Sandeep.
            Language Rules:
            1. If user asks in Hindi or Hinglish, respond clearly in natural Hinglish or Hindi.
            2. Keep answers concise, direct, structured, and easy to read.
            """
            
            if file_attached and file_type == "image":
                prompt_text = f"{system_instruction}\n\nUser Question: {user_query}\n\nExplain the diagram/image briefly and clearly."
                payload = [prompt_text, file_obj]
            elif file_attached and file_type == "pdf":
                if not pdf_extracted_text.strip():
                    full_response = "⚠️ Is PDF mein text select nahi ho raha (scanned image PDF hai)."
                    message_placeholder.markdown(full_response)
                    payload = None
                else:
                    prompt_text = f"{system_instruction}\n\nPDF Text:\n{pdf_extracted_text[:3000]}\n\nQuestion: {user_query}"
                    payload = prompt_text
            else:
                prompt_text = f"{system_instruction}\n\nUser Question: {user_query}"
                payload = prompt_text

            if payload:
                final_answer = generate_safe_response(payload, message_placeholder)
            else:
                final_answer = full_response

        except Exception as e:
            final_answer = f"⚠️ **Execution Error:** {str(e)}"
            message_placeholder.markdown(final_answer)

        current_messages.append({"role": "assistant", "content": final_answer})
        st.session_state.chats[st.session_state.current_chat_id] = current_messages
        save_all_chats(st.session_state.chats)
