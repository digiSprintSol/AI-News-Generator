import streamlit as st
import requests
from datetime import datetime
import streamlit.components.v1 as components
import base64
from docx import Document
from io import BytesIO

API_URL = "https://app.thub.tech/api/v1/prediction/2268e882-0038-47e4-9de0-646ba53030e5"

def query(payload):
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()

if "news" not in st.session_state:
    st.session_state.news = None
if "generation_count" not in st.session_state:
    st.session_state.generation_count = 0
if "last_generated_date" not in st.session_state:
    st.session_state.last_generated_date = None


with open("resources/digitalsprint_logo.jpg", "rb") as file:
    img_bytes = file.read()

img_base64_encoding = base64.b64encode(img_bytes).decode()
st.markdown(f"""
<div style="display: flex; align-items: center;">
    <img src="data:image/png;base64,{img_base64_encoding}" width="40">
    <h2 style="margin-left: 10px;">DigitalSprint AI News Generator</h2>
</div>
""", unsafe_allow_html=True)


st.set_page_config(
    page_title="DigitalSprint AI News Generator",
    page_icon="resources/digitalsprint_logo.jpg"  
)

today = datetime.now().date()
print(today,"Hellllllllllllllllllllllllllllllllllllllllllllllllllllllllllll")
print(st.session_state.last_generated_date)
if st.session_state.last_generated_date != today:
    st.session_state.generation_count = 0
    st.session_state.news = None
    # st.session_state.last_generated_date = today

prompt = '''User Request: Find the latest AI knowledge and generate a LinkedIn post.
Instructions:
- Treat this as a fresh, standalone task.
- Collect and extract at least 5 distinct news items from different sources.
- Generate a professional LinkedIn post combining all findings.
- Call make_webhook exactly once with the final post.
- Do not call make_webhook more than once per day.
- After calling it, return exactly: Post published.
- Ignore previous make_webhook calls from earlier prompts.'''

if st.button("Generate AI News"):
    if st.session_state.generation_count >= 1:
        st.error("News was already generated for the day and this news is from the session storage where news was stored when it was generated for the first time in the day.")
    else:
        if st.session_state.news:
            st.session_state.generation_count += 1
        if not st.session_state.news: 
            try:
                result = query({"question": prompt})
                agent = [agent for agent in result["agentReasoning"] if "Autonomous LinkedIn Content Publisher Agent" in agent["agentName"]][0]
                target_tool = [tool for tool in agent["usedTools"] if tool["tool"] == "make_webhook"][0]
                st.session_state.news = target_tool["toolInput"]["message"]
                st.session_state.generation_count += 1
                st.session_state.last_generated_date = today
                st.success("News generated successfully!")    
            except Exception as e:
                st.error(f"API call failed: {e}")
                st.stop()

if st.session_state.news:
    docx = Document()
    docx.add_paragraph(st.session_state.news)
    docx_buffer = BytesIO()
    docx.save(docx_buffer)
    docx_buffer.seek(0)
    
   

    st.markdown(
        f"""
        <div style='padding:12px; background-color:black; color:white;
                    border-radius:8px; font-size:16px; line-height:1.5;'>
            {st.session_state.news}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    components.html(
        f"""
        <textarea id="hidden-news" style="position:absolute; left:-9999px;">{st.session_state.news}</textarea>
        <button onclick="
            var copyText = document.getElementById('hidden-news');
            copyText.select();
            document.execCommand('copy');
            document.getElementById('copy-message').innerText = ' News copied to clipboard!';
        " 
        style="margin-top:10px; padding:8px 14px; background-color:#4CAF50; 
               color:white; border:none; border-radius:5px; cursor:pointer;">
             Copy News
        </button>
        <a download='ai_news.docx' 
               href='data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{base64.b64encode(docx_buffer.getvalue()).decode()}'
               style="padding:8px 14px; background-color:#4CAF50; 
                      color:white; border:none; border-radius:5px; cursor:pointer; font-size:14px; text-decoration:none; text-align:center; margin-left : 10px">
               Download News
            </a>
        <div id="copy-message" style="margin-top:8px; font-size:14px; color:white;"></div>
        """,
        height=80
    )
