import streamlit as st
import requests
from datetime import datetime
from pathlib import Path
import base64
from docx import Document
from io import BytesIO
import json
import streamlit.components.v1 as components


API_URL = "https://app.thub.tech/api/v1/prediction/2268e882-0038-47e4-9de0-646ba53030e5"  
RESOURCES_DIR = Path("resources")
RESOURCES_DIR.mkdir(exist_ok=True)

def query(payload):
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()

def get_today_file():
    today_str = datetime.now().strftime("%Y-%m-%d")
    return RESOURCES_DIR / f"news_{today_str}.json"

def load_today_news():
    file_path = get_today_file()
    if file_path.exists():
        with open(file_path, "r") as f:
            data = json.load(f)
        return data.get("news")
    return None

def save_today_news(news):
    file_path = get_today_file()
    with open(file_path, "w") as f:
        json.dump({"news": news}, f)

def clear_today_news():
    file_path = get_today_file()
    if file_path.exists():
        file_path.unlink()
    st.session_state.news = None
    st.session_state.news_date = None

def remove_old_files():
    today_file = get_today_file()
    for file in RESOURCES_DIR.glob("news_*.json"):
        if file != today_file:
            file.unlink()


with open("resources/digitalsprint_logo.jpg", "rb") as file:
    img_bytes = file.read()
img_base64_encoding = base64.b64encode(img_bytes).decode()

st.set_page_config(page_title="DigitalSprint AI News Generator", page_icon="resources/digitalsprint_logo.jpg")

st.markdown(f"""
<div style="display: flex; align-items: center;">
    <img src="data:image/png;base64,{img_base64_encoding}" width="40">
    <h2 style="margin-left: 10px;">DigitalSprint AI News Generator</h2>
</div>
""", unsafe_allow_html=True)


today_str = datetime.now().strftime("%Y-%m-%d")
if "news" not in st.session_state:
    st.session_state.news = None
if "news_date" not in st.session_state:
    st.session_state.news_date = None


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
    if st.session_state.news and st.session_state.news_date == today_str:
        st.warning("News already generated for today. Clear news to regenerate.")
    else:
        news_from_file = load_today_news()
        if news_from_file:
            st.session_state.news = news_from_file
            st.session_state.news_date = today_str
            st.warning("News already generated for today. Clear news to regenerate.")
        else:
            try:
                remove_old_files()
                result = query({"question": prompt})
                agent = [agent for agent in result["agentReasoning"] if "Autonomous LinkedIn Content Publisher Agent" in agent["agentName"]][0]
                target_tool = [tool for tool in agent["usedTools"] if tool["tool"] == "make_webhook"][0]
                news = target_tool["toolInput"]["message"]
                st.session_state.news = news
                st.session_state.news_date = today_str
                save_today_news(news)
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
                    border-radius:8px; font-size:16px; line-height:1.5;'>{st.session_state.news}</div>
        """,
        unsafe_allow_html=True
    )

    components.html(
        f"""
        <textarea id="hidden-news" style="position:absolute; left:-9999px;">{st.session_state.news}</textarea>
        <div style="margin-top:10px; display:flex; gap:10px; flex-wrap:nowrap;">
            
            <!-- Copy News -->
            <button onclick="
                var t=document.getElementById('hidden-news');
                t.select();
                document.execCommand('copy');
                document.getElementById('copy-message').innerText=' News copied to clipboard!';
            " style="padding:8px 14px;background-color:#4CAF50;
                     color:white;border:none;border-radius:5px;cursor:pointer;
                     font-size:14px;white-space:nowrap;">
                Copy News
            </button>

            <!-- Download News -->
            <a download='ai_news.docx'
               href='data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{base64.b64encode(docx_buffer.getvalue()).decode()}'
               style="padding:8px 14px;background-color:#4CAF50;color:white;border:none;border-radius:5px;cursor:pointer;
                      font-size:14px;text-decoration:none;text-align:center;
                      white-space:nowrap; display:inline-flex; align-items:center; justify-content:center;">
               Download News
            </a>
        </div>
        <div id="copy-message" style="margin-top:8px;font-size:14px;color:white;"></div>
        """,
        height=100
    )

    clear_col = st.container()
    with clear_col:
        if st.button("Clear News", key="clear_news_streamlit"):
            clear_today_news()
            st.session_state.cleared = True
            st.rerun()

if st.session_state.get("cleared", False):
    st.success("News cleared. You can now re-generate the news.")
    del st.session_state["cleared"]
