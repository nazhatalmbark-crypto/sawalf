import hashlib
import html
from datetime import datetime
import random
import sqlite3
import streamlit as st

DB_PATH = "/tmp/sawalf_smart_v4.db"


def get_connection():
  return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
  try:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT,
                username TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                msg_hash TEXT
            )
        """)
    conn.commit()
    conn.close()
  except Exception:
    pass


init_db()

st.set_page_config(
    page_title="منصة سوالف الذكية", page_icon="💬", layout="centered"
)

st.title("💬 تطبيق سوالف - الذكي الحقيقي")
st.write(
    "دردشة حية بقاعدة بيانات، وبوت يفهم كلامك ويرد عليك حسب سياق الحچي!"
)

st.sidebar.header("إعدادات الجلسة")
username = st.sidebar.text_input("اسمك الكريم:", "صديق سوالف")

room_choice = st.sidebar.selectbox(
    "اختر غرفة المحادثة:",
    [
        "الدردشة العامة (Global)",
        "استراحة الشباب (Random)",
        "سوالف خاصة (Private)",
    ],
)

BAD_WORDS = ["حيوان", "غبي", "زبالة", "ساقط", "فاشل", "كلب"]


def load_messages(room):
  try:
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT username, role, content, timestamp, msg_hash FROM messages"
        " WHERE room = ?",
        (room,),
    )
    rows = c.fetchall()
    conn.close()
    return rows
  except Exception:
    return []


def save_message(room, uname, role, content):
  sanitized_content = html.escape(content)
  sanitized_uname = html.escape(uname)
  current_time = datetime.now().strftime("%I:%M %p")
  msg_signature = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]

  init_db()
  conn = get_connection()
  c = conn.cursor()
  c.execute(
      "INSERT INTO messages (room, username, role, content, timestamp, "
      "msg_hash) VALUES (?, ?, ?, ?, ?, ?)",
      (
          room,
          sanitized_uname,
          role,
          sanitized_content,
          current_time,
          msg_signature,
      ),
  )
  conn.commit()
  conn.close()


st.subheader(f"📍 أنت الآن في: {room_choice}")

messages = load_messages(room_choice)
for uname, role, content, timestamp, msg_hash in messages:
  with st.chat_message(role):
    st.markdown(f"**{uname}** `[{timestamp}]`:")
    st.markdown(content)

if prompt := st.chat_input(f"اكتب رسالتك في {room_choice}..."):
  if not username.strip():
    username = "مستخدم مجهول"

  # فحص التجاوز
  is_bad = False
  if "العامة" in room_choice:
    for word in BAD_WORDS:
      if word in prompt:
        is_bad = True
        break

  save_message(room_choice, username, "user", prompt)

  if is_bad:
    alert_msg = (
        f"⚠️ عذراً يا {username}, ممنوع التجاوز بالألفاظ هنا. احترم السادة الموجودين!"
    )
    save_message(room_choice, "مدير النظام", "assistant", alert_msg)
  else:
    # **هنا الذكاء الحقيقي: البوت يقرأ ويجاوب حسب الكلمة!**
    user_text = prompt.lower()

    if "السلام عليكم" in user_text or "سلام عليكم" in user_text:
      bot_reply = (
          f"وعليكم السلام ورحمة الله وبركاته يا هلا بيك يا {username}، منورنا!"
      )
    elif "هلو" in user_text or "هلا" in user_text or "اهلاً" in user_text:
      bot_reply = (
          f"هلا بيك وبكل اهلنا يا {username}! شلونك اليوم؟ عساك بخير."
      )
    elif "شلونك" in user_text or "شخبارك" in user_text:
      bot_reply = (
          f"الحمد لله بخير مادامك موجود وتسأل يا {username}. انت طمني عنك؟"
    )
    elif "اي" in user_text or "نعم" in user_text or "صح" in user_text:
      bot_reply = f"عاشت ايدك يا {username}، زين تسوي."
    else:
      # رد عام إذا ما لقى كلمة مفتاحية
      general_replies = [
          f"افتهمت قصدك يا {username}، كمل وياي شنو عندك بعد؟",
          f"حلو كلش يا {username}، سولفلي بعد خل نسمعك.",
          (
              f"ممم.. صدك والله يا {username}، هذا الشي يخلي الواحد يفكر بيه."
          ),
      ]
      bot_reply = random.choice(general_replies)

    save_message(room_choice, "مساعد سوالف", "assistant", bot_reply)

  st.rerun()
