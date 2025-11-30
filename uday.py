import streamlit as st
import time
import os
import json
import re
import google.generativeai as genai
from datetime import datetime
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
import random

# — NLTK setup —
try:
    nltk.data.find("sentiment/vader_lexicon")
except:
    nltk.download("vader_lexicon")

# — API Key —
GEMINI_API_KEY = "AIzaSyB_1mLJEtCnNrcVBY5bV1OfkW3gOZ0wf88"  # <--- your key


# ----------------- Crisis / Screener / Chatbot logic -----------------
class CrisisManager:
    def __init__(self, model):
        self.model = model
        self.keywords = [
            "suicide", "kill myself", "want to die", "end my life",
            "self harm", "hurt myself", "cutting", "no reason to live"
        ]
        self.response = (
            "💙 I’m really sorry you’re feeling this way.\n"
            "You're not alone. Please reach out for support immediately:\n\n"
            "📞 KIRAN Helpline (India): 1800-599-0019\n"
            "📞 iCALL: 022-25521111\n\n"
            "You matter. 💙"
        )

    def check(self, text):
        if any(k in text.lower() for k in self.keywords):
            return self.response
        return None


class Screener:
    def __init__(self):
        self.questions = [
            "In the last 2 weeks, how often have you been anxious or on edge?",
            "How often have you been unable to control worrying?",
            "How often have you been worrying too much about different things?",
            "How often have you had trouble relaxing?",
            "How often have you been restless or unable to sit still?",
            "How often have you become easily irritable?",
            "How often have you felt afraid as if something awful might happen?"
        ]
        self.idx = 0
        self.score = 0
        self.active = False
        self.completed = False

    def start(self):
        self.active = True
        self.idx = 0
        self.score = 0
        return "🧠 Let's begin a short screening check-in."

    def process(self, value):
        self.score += int(value)
        self.idx += 1
        if self.idx < len(self.questions):
            return self.questions[self.idx]

        self.active = False
        self.completed = True
        level = ["Minimal", "Mild", "Moderate", "Severe"][min(self.score // 5, 3)]
        return f"🧠 Your anxiety level is **{level}** (Score: {self.score})."


class Chatbot:
    def __init__(self, email, profile):
        self.profile = profile
        self.email = email
        self.sia = SentimentIntensityAnalyzer()

        safe = re.sub(r"[^a-zA-Z0-9]", "_", email)
        self.history_file = f"history_{safe}.json"

        genai.configure(api_key=GEMINI_API_KEY)
        self.base = genai.GenerativeModel("gemini-2.5-flash")
        self.crisis = CrisisManager(self.base)
        self.screen = Screener()

        system = f"""
        You are UDAY — a compassionate mental wellness AI companion.
        Be supportive, warm, and human. Never diagnose. Offer grounding when needed.

        USER PROFILE:
        Name: {profile['name']}
        Age: {profile['age']}
        Profession: {profile['profession']}
        Focus: {profile['focus']}
        """

        self.model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system)
        self.chat = self.model.start_chat(history=self.load_history())

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                return json.load(open(self.history_file))
            except Exception:
                return []
        return []

    def save_history(self):
        history = [
            {"role": m.role, "parts": [p.text for p in m.parts]}
            for m in self.chat.history
        ]
        json.dump(history, open(self.history_file, "w"), indent=2)

    def respond(self, text):
        if self.screen.active:
            return self.screen.process(text)

        if "screening" in text.lower() and not self.screen.completed:
            return self.screen.start()

        crisis = self.crisis.check(text)
        if crisis:
            return crisis

        if self.sia.polarity_scores(text)['compound'] < -0.4:
            text += " [Emotionally low — respond gently]"

        reply = self.chat.send_message(text).text
        self.save_history()
        return reply


# ---------------------- CSS Theme ----------------------
st.markdown("""
<style>
body {
  background: linear-gradient(135deg, #F5F5F5, #E8F3F1);
  background-size: 300% 300%;
  animation: bgAnim 20s ease infinite;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #080808;
}
@keyframes bgAnim {
  0% {background-position: 0% 50%;}
  50% {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}

h1, h2, h3, h4, h5, h6 {
  color: #064E40 !important;
  font-weight: 800;
}

.splash {
  text-align:center;
  font-size: 48px;
  font-weight: 900;
  color: #064E40;
  padding-top: 200px;
}

.chat-row { display:flex; margin:10px 0; }
.chat-row-user { justify-content:flex-end; }
.chat-row-bot  { justify-content:flex-start; }

/* SAME SPACE + HORIZONTAL WRAP FOR BOTH BUBBLES */
.chat-bubble-user,
.chat-bubble-bot {
  max-width: 60%;
  /* REMOVED: min-width: 35%; */            
  display: inline-block;
  word-wrap: break-word;
  white-space: normal;
  padding: 12px 18px;
  line-height: 1.4;
  font-size: 15px;
  text-align: left;
}

/* User bubble style */
.chat-bubble-user {
  background:#064E40;
  color:white;
  border-radius:18px 18px 4px 18px;
}

/* Bot bubble style */
.chat-bubble-bot {
  background:#E5E7EB;
  color:#080808;
  border-radius:18px 18px 18px 4px;
}

.msg-time { font-size:11px; color:#555; margin-top:2px; }
.typing { font-size:14px; font-style:italic; color:#333; }

.stButton>button {
  background-color:#064E40;
  color:white; font-weight:600;
  padding:10px 20px;
  border-radius:10px;
  border:none;
}

.highlight-q { font-size:22px; font-weight:700; color:#064E40; }
.q-text { font-size:18px; font-weight:600; color:#080808; }

.card {
  background:white;
  padding:20px;
  border-radius:12px;
  box-shadow:0 6px 18px rgba(0,0,0,0.1);
  text-align:center;
}

.breath-circle {
  width:160px;
  height:160px;
  border-radius:50%;
  margin: 20px auto;
  border:4px solid #064E40;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight:700;
  color:#064E40;
}
</style>
""", unsafe_allow_html=True)


# ---------------------- Streamlit State ----------------------
if "splash" not in st.session_state: st.session_state.splash = True
if "stage" not in st.session_state: st.session_state.stage = "intro"   # intro, login, register, chat, dashboard, breathing
if "bot" not in st.session_state: st.session_state.bot = None
if "messages" not in st.session_state: st.session_state.messages = []
if "welcome_sent" not in st.session_state: st.session_state.welcome_sent = False
if "screen_button_used" not in st.session_state: st.session_state.screen_button_used = False
if "pending_text" not in st.session_state: st.session_state.pending_text = None
if "profile" not in st.session_state: st.session_state.profile = None


# ---------------------- Splash page ----------------------
if st.session_state.splash:
    st.markdown("<div class='splash'>💚 Welcome to UDAY — Your Mental Wellness Companion 💚</div>",
                unsafe_allow_html=True)
    time.sleep(2.5)
    st.session_state.splash = False
    st.rerun()


# ---------------------- Intro ----------------------
if st.session_state.stage == "intro":
    st.header("Have you used UDAY before?")
    choice = st.radio("Select", ["Yes", "No"], horizontal=True, key="intro_radio")
    if st.button("Continue"):
        st.session_state.stage = "login" if choice == "Yes" else "register"
        st.rerun()


# ---------------------- Login ----------------------
elif st.session_state.stage == "login":
    st.header("🔐 Login")
    email = st.text_input("Email")
    if st.button("Login"):
        if os.path.exists("users.json"):
            users = json.load(open("users.json"))
            if email in users:
                st.session_state.profile = users[email]
                st.session_state.bot = Chatbot(email, users[email])
                st.session_state.stage = "chat"
                st.rerun()
        st.error("User not found!")


# ---------------------- Register ----------------------
elif st.session_state.stage == "register":
    st.header("🧾 Create Account")
    email = st.text_input("Email ID")
    name = st.text_input("Name")
    age = st.text_input("Age")
    profession = st.selectbox("Profession", ["Student", "Corporate", "Worker", "Homemaker", "Self-employed", "Other"])
    focus = st.selectbox("Focus Area", ["Anxiety", "Work Stress", "Depression", "Self-esteem", "Relationships", "Overthinking"])

    if st.button("Register & Start"):
        users = json.load(open("users.json")) if os.path.exists("users.json") else {}
        users[email] = {"name": name, "age": age, "profession": profession, "focus": focus}
        json.dump(users, open("users.json", "w"), indent=2)

        st.session_state.profile = users[email]
        st.session_state.bot = Chatbot(email, users[email])
        st.session_state.stage = "chat"
        st.rerun()


# ---------------------- Chat Screen ----------------------
elif st.session_state.stage == "chat":
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header("💬 Chat with UDAY")
    with col2:
        if st.button("📊 Dashboard"):
            st.session_state.stage = "dashboard"
            st.rerun()
    with col3:
        if st.button("🌬️ Breathing"):
            st.session_state.stage = "breathing"
            st.rerun()

    # Welcome message
    if not st.session_state.welcome_sent:
        w = f"Hi {st.session_state.profile['name']}! 😊 I’m glad you're here. How are you feeling today?"
        ts = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "assistant", "content": w, "time": ts})
        st.session_state.welcome_sent = True

    # Show chat history
    for msg in st.session_state.messages:
        role, content, t = msg["role"], msg["content"], msg["time"]
        direction = "chat-row-user" if role == "user" else "chat-row-bot"
        bubble = "chat-bubble-user" if role == "user" else "chat-bubble-bot"
        align = "right" if role == "user" else "left"
        st.markdown(
            f"""
            <div class="chat-row {direction}">
              <div>
                <div class="{bubble}">{content}</div>
                <div class="msg-time" style="text-align:{align};">{t}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # If pending user text exists → bot reply now
    if st.session_state.pending_text:
        pending = st.session_state.pending_text
        st.session_state.pending_text = None

        typing = st.empty()
        for i in range(3):
            typing.markdown(
                f"<p class='typing'>UDAY is typing{'.' * ((i % 3) + 1)}</p>",
                unsafe_allow_html=True
            )
            time.sleep(0.3)

        reply = st.session_state.bot.respond(pending)
        ts2 = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "assistant", "content": reply, "time": ts2})
        st.rerun()

    # SCREENING MODE
    if st.session_state.bot.screen.active:
        q = st.session_state.bot.screen.questions[st.session_state.bot.screen.idx]
        st.markdown(
            f"<p class='highlight-q'>🧠 Screening Question {st.session_state.bot.screen.idx + 1}</p>",
            unsafe_allow_html=True
        )
        st.markdown(f"<p class='q-text'>{q}</p>", unsafe_allow_html=True)

        opt = st.radio(
            "Choose an answer:",
            ["0 - Not at all", "1 - Several days", "2 - More than half the days", "3 - Nearly every day"],
            key=f"screen_{st.session_state.bot.screen.idx}"
        )

        if st.button("Submit Answer"):
            val = opt.split(" ")[0]
            ts = datetime.now().strftime("%H:%M")
            st.session_state.messages.append({"role": "user", "content": val, "time": ts})

            reply = st.session_state.bot.screen.process(val)
            ts2 = datetime.now().strftime("%H:%M")
            st.session_state.messages.append({"role": "assistant", "content": reply, "time": ts2})

            if st.session_state.bot.screen.completed:
                st.session_state.screen_button_used = True

            st.rerun()

    else:
        # Screening button (one-time)
        if not st.session_state.screen_button_used:
            if st.button("🧠 Start Anxiety Screening"):
                resp = st.session_state.bot.screen.start()
                ts = datetime.now().strftime("%H:%M")
                st.session_state.messages.append({"role": "assistant", "content": resp, "time": ts})
                st.session_state.screen_button_used = True
                st.rerun()

        # Normal chat input
        user_text = st.chat_input("Type your message…")

        if user_text:
            ts = datetime.now().strftime("%H:%M")
            st.session_state.messages.append({"role": "user", "content": user_text, "time": ts})
            st.session_state.pending_text = user_text
            st.rerun()


# ---------------------- Dashboard ----------------------
elif st.session_state.stage == "dashboard":
    st.header("📊 Emotional Wellness Dashboard")

    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown("<div class='card'><h4>Mood Trend</h4><p>😊 Improving</p></div>", unsafe_allow_html=True)
    with colB:
        st.markdown("<div class='card'><h4>Chat Sessions</h4><p>7</p></div>", unsafe_allow_html=True)
    with colC:
        st.markdown("<div class='card'><h4>Wellness Score</h4><p>81%</p></div>", unsafe_allow_html=True)

    if st.button("⬅ Back to Chat"):
        st.session_state.stage = "chat"
        st.rerun()

    st.subheader("Weekly Mood Pattern")
    df = pd.DataFrame({
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Score": [random.randint(40, 90) for _ in range(7)]
    })
    st.line_chart(df.set_index("Day"))


# ---------------------- Breathing Exercise Screen ----------------------
elif st.session_state.stage == "breathing":
    st.header("🌬️ Guided Breathing Exercise")

    st.markdown(
        "Take a minute to slow down. We'll do a simple 4-4-4-4 box breathing pattern:\n\n"
        "- Inhale for 4 seconds\n"
        "- Hold for 4 seconds\n"
        "- Exhale for 4 seconds\n"
        "- Hold for 4 seconds\n"
    )

    start = st.button("Start 1-Minute Breathing")

    if start:
        placeholder_text = st.empty()
        placeholder_circle = st.empty()

        cycles = 4
        for _ in range(cycles):
            for label in [("🌱 Inhale gently...", 4),
                          ("🤍 Hold...", 4),
                          ("🌬️ Exhale slowly...", 4),
                          ("🤍 Hold...", 4)]:
                text, sec = label
                for i in range(sec, 0, -1):
                    placeholder_text.markdown(f"### {text}")
                    placeholder_circle.markdown(
                        f"<div class='breath-circle'>{i}</div>", unsafe_allow_html=True
                    )
                    time.sleep(1)

        placeholder_text.markdown("### 🤗 Nice job. Notice how your body feels right now.")
        placeholder_circle.empty()

    if st.button("⬅ Back to Chat"):
        st.session_state.stage = "chat"
        st.rerun()
