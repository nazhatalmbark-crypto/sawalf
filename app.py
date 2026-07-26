import hashlib
import html
from datetime import datetime
import random
import sqlite3
import streamlit as st

DB_PATH = "/tmp/sawalf_pro_v5.db"


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
    page_title="منصة سوالف العراقية", page_icon="💬", layout="centered"
)

st.title("💬 تطبيق سوالف - الإصدار المطور")
st.write(
    "دردشة حية مع غرف منفصلة (بنات، شباب، مختلط) ونظام دردشة خاصة (الخاص بين"
    " الأعضاء)!"
)

# لوحة التحكم الجانبية
st.sidebar.header("إعدادات الجلسة")
username = st.sidebar.text_input("اسمك الكريم:", "صديق سوالف")

room_options = [
    "الدردشة العامة (Global)",
    "غرفة البنات فقط 🌸",
    "غرفة الشباب فقط 🎮",
    "الدردشة المختلطة 🌐",
    "محادثة خاصة (Direct Message)",
]

room_choice = st.sidebar.selectbox("اختر غرفة المحادثة:", room_options)

# تحديد الغرفة الفعلية في حال اختيار الخاص
actual_room = room_choice
if "محادثة خاصة" in room_choice:
  target_user = st.sidebar.text_input("اكتب اسم الشخص للدردشة الخاصة معهم:")
  if target_user.strip():
    # دمج وترتيب الأسماء حتى يكون اسم الغرفة الخاصة ثابت وموحد للطرفين
    users_sorted = sorted(
        [username.strip().lower(), target_user.strip().lower()]
    )
    actual_room = f"DM_{users_sorted[0]}_{users_sorted[1]}"
    st.sidebar.info(f"🔒 محادثة خاصة نشطة مع: {target_user}")
  else:
    actual_room = "DM_Waiting"
    st.sidebar.warning("يرجى كتابة اسم الشخص في الحقل أعلاه لبدء المحادثة الخاصة.")

# قائمة الكلمات الممنوعة للدردشة العامة
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

messages = load_messages(actual_room)
for uname, role, content, timestamp, msg_hash in messages:
  with st.chat_message(role):
    st.markdown(f"**{uname}** `[{timestamp}]`:")
    st.markdown(content)

if prompt := st.chat_input("اكتب رسالتك هنا..."):
  if not username.strip():
    username = "مستخدم مجهول"

  if "محادثة خاصة" in room_choice and actual_room == "DM_Waiting":
    st.error("يرجى إدخال اسم الشخص المطلوب في القائمة الجانبية أولاً!")
  else:
    # فحص التجاوز فقط في الغرف العامة أو المختلطة
    is_bad = False
    if "العامة" in room_choice or "المختلطة" in room_choice:
      for word in BAD_WORDS:
        if word in prompt:
          is_bad = True
          break

    save_message(actual_room, username, "user", prompt)

    if is_bad:
      alert_msg = f"⚠️ عذراً يا {username}, الألفاظ النابية ممنوعة هنا. التزم بالآداب!"
      save_message(actual_room, "مدير النظام", "assistant", alert_msg)
    elif "محادثة خاصة" not in room_choice:
      # ردود البوت الذكية في الغرف العامة
      user_text = prompt.lower()
      if "السلام عليكم" in user_text or "سلام عليكم" in user_text:
        bot_reply = (
            f"وعليكم السلام ورحمة الله وبركاته يا هلا بيك يا {username}!"
        )
      elif "هلو" in user_text or "هلا" in user_text:
        bot_reply = f"هلا بيك وبكل اهلنا يا {username}! منور الغرفة."
      elif "شلونك" in user_text or "شخبارك" in user_text:
        bot_reply = f"الحمد لله بخير مادامك موجود وتسأل يا {username}."
      else:
        general_replies = [
            f"افتهمت قصدك يا {username}، كمل وياي شنو عندك بعد؟",
            f"حلو كلش يا {username}، تسلم على هالمشاركة.",
            f"ممم.. صدك والله يا {username}.",
        ]
        bot_reply = random.choice(general_replies)
      save_message(actual_room, "مساعد سوالف", "assistant", bot_reply)

    st.rerun()
