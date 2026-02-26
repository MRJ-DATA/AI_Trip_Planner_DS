import streamlit as st
import requests
import datetime

BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="🌍 Travel Planner Agentic Application",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("🌍 Travel Planner Agentic Application")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.header("How can I help you in planning a trip?")

with st.form(key="query_form", clear_on_submit=True):
    user_input = st.text_input(
        "User Input",
        placeholder="e.g. Plan a trip to Goa for 5 days"
    )
    submit_button = st.form_submit_button("Send")

if submit_button and user_input.strip():
    try:
        with st.spinner("Bot is thinking..."):
            payload = {"question": user_input}
            response = requests.post(f"{BASE_URL}/query", json=payload)

        if response.status_code == 200:
            data = response.json()

            answer = data.get("answer", "No answer returned.")
            best_itinerary = data.get("best_itinerary")
            satisfaction_score = data.get("satisfaction_score")

            markdown_content = f"""
## 🌍 AI Travel Plan
**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M')}

---

{answer}

---
"""
            st.markdown(markdown_content)

            if satisfaction_score is not None:
                st.success(
                    f"✅ Predicted User Satisfaction Score: **{round(satisfaction_score * 100, 2)}%**"
                )

            if best_itinerary is not None:
                with st.expander("📊 Optimized Itinerary (Data-Driven Selection)"):
                    st.json(best_itinerary)

        else:
            st.error("Bot failed to respond: " + response.text)

    except Exception as e:
        st.exception(e)