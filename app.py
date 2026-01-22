import streamlit as st
import requests
import base64
from PIL import Image
import json

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000/ask"
PAGE_TITLE = "Sampurna IT Support"
PAGE_ICON = "🚀"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

st.markdown("""
<style>
    .stChatMessage { border-radius: 15px; padding: 10px; }
    .stTextInput input { border-radius: 20px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def encode_image_to_base64(image_file):
    if image_file is not None:
        bytes_data = image_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode('utf-8')
        mime_type = image_file.type
        return f"data:{mime_type};base64,{base64_str}"
    return None

def build_last5_history(messages):
    """
    Last 5 chat items as backend expects: List[str]
    We keep last 5 *messages* (user+assistant), because backend already slices too.
    """
    last_msgs = messages[-5:] if len(messages) > 5 else messages
    return [f"{m['role']}: {m['content']}" for m in last_msgs]

def export_chat_txt(messages):
    lines = []
    for m in messages:
        role = "USER" if m["role"] == "user" else "ASSISTANT"
        lines.append(f"{role}: {m['content']}\n")
    return "\n".join(lines).strip()

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am Sampurna IT Support. You can upload a screenshot of your error or ask me a question."}
    ]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

with st.sidebar:
    st.title(f"{PAGE_ICON} Sampurna IT")
    st.markdown("Powered by **Gemini 2.0 Vision**")
    st.divider()

    st.markdown("### 📸 Upload Screenshot")
    uploaded_file = st.file_uploader(
        "Upload an image (PNG/JPG)",
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{st.session_state.uploader_key}"
    )

    image_base64 = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        image_base64 = encode_image_to_base64(uploaded_file)
        st.success("Image ready to send!")

    st.divider()

    # ✅ Download buttons (NEW)
    chat_txt = export_chat_txt(st.session_state.messages)
    chat_json = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)

    st.download_button(
        "⬇️ Download Chat (TXT)",
        data=chat_txt,
        file_name="sampurna_chat.txt",
        mime="text/plain",
        use_container_width=True
    )
    st.download_button(
        "⬇️ Download Chat (JSON)",
        data=chat_json,
        file_name="sampurna_chat.json",
        mime="application/json",
        use_container_width=True
    )

    st.divider()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am Sampurna IT Support. You can upload a screenshot of your error or ask me a question."}
        ]
        st.session_state.uploader_key += 1
        st.rerun()

# --- Main Chat ---
st.title("Sampurna IT Support 🚀")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Describe your issue..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                history_list = build_last5_history(st.session_state.messages)

                payload = {
                    "question": prompt,
                    "chat_history": history_list,   # ✅ last 5 context memory
                    "image_data": image_base64
                }

                response = requests.post(BACKEND_URL, json=payload, timeout=60)

                if response.status_code == 200:
                    answer = response.json().get("answer", "").strip()
                    if not answer:
                        answer = "No answer received."

                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                    # auto-clear uploaded image after use
                    if image_base64:
                        st.session_state.uploader_key += 1
                        st.rerun()
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to Backend. Is it running?")
            except requests.exceptions.Timeout:
                st.error("⏳ Backend timed out. Please try again.")
