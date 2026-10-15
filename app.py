import os
import json
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
        * 🤖 **Gemini AI Core (3.8 Flash)**
        * 📁 **PDF Notes RAG Parsing**
        """)

    with st.expander("⚙️ System Health"):
        st.markdown("""
        * **Engine:** Gemini-3.8-Flash Active
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

# API Key Setup securely using Streamlit Secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error("⚠️ GEMINI_API_KEY not found in Streamlit Secrets! Please add your valid key in app settings.")
    st.stop()

# Set model to gemini-3.8-flash as specified by API
def get_working_gemini_model():
    return genai.GenerativeModel('gemini-3.8-flash')

# Display active chat history
current_messages = st.session_state.chats[st.session_state.current_chat_id]
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Layout: Chat Input + PDF Upload
col1, col2, col3 = st.columns([0.70, 0.15, 0.15])

with col3:
    uploaded_pdf = st.file_uploader("PDF Notes", type=["pdf"], label_visibility="collapsed")

with col1:
    user_query = st.chat_input("SandX-Node se kuch bhi puchein ya notes upload karein...")

# File Processing Logic
file_attached = False
file_type = ""
file_name = ""
pdf_extracted_text = ""

if uploaded_pdf is not None:
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
        st.error(f"PDF read karne mein error aayi: {str(e)}")

# Main Trigger
if user_query:
    display_content = f"📁 *[Attached {file_type.upper()}: {file_name}]* \n\n {user_query}" if file_attached else user_query

    current_messages.append({"role": "user", "content": display_content})
    st.session_state.chats[st.session_state.current_chat_id] = current_messages
    save_all_chats(st.session_state.chats)

    with st.chat_message("user"):
        st.markdown(display_content)

    with st.chat_message("assistant"):
        with st.spinner("SandX-OmniNode analyze kar raha hai..."):
            try:
                active_model = get_working_gemini_model()
                
                system_instruction = """
                You are SandX-OmniNode AI created by Sandeep.
                Language Rules:
                1. If the user asks in Hindi or Hinglish, respond clearly in natural Hinglish or Hindi.
                2. If the user asks in English, respond in clear English.
                3. Maintain clean markdown formatting with headings and bullet points.
                """
                
                if file_attached and file_type == "pdf":
                    if not pdf_extracted_text.strip():
                        final_answer = "⚠️ Is PDF mein text select nahi ho raha (yeh scanned image PDF hai)."
                    else:
                        prompt_text = f"{system_instruction}\n\nUploaded PDF Content:\n{pdf_extracted_text[:4000]}\n\nUser Question: {user_query}\n\nAnswer the user question based on the uploaded PDF content above."
                        response = active_model.generate_content(prompt_text)
                        final_answer = response.text
                else:
                    prompt_text = f"{system_instruction}\n\nUser Question: {user_query}"
                    response = active_model.generate_content(prompt_text)
                    final_answer = response.text

            except Exception as e:
                final_answer = f"⚠️ **Execution Error:** {str(e)}"

            st.markdown(final_answer)
            current_messages.append({"role": "assistant", "content": final_answer})
            st.session_state.chats[st.session_state.current_chat_id] = current_messages
            save_all_chats(st.session_state.chats)
