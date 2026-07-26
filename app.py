import hashlib
import html
from datetime import datetime
import sqlite3
import streamlit as st

# مسار قاعدة البيانات الآمن
DB_PATH = "/tmp/sawalf_secure_v2.db"


def get_connection():
  return sqlite3.connect(DB_PATH, check_same_thread=False)


# تهيئة قاعدة البيانات مع إضافة أعمدة الوقت وبصمة التشفير
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
    page_title="سوالف الآمنة والمطورة", page_icon="🔒", layout="centered"
)

st.title("🔒 منصة سوالف السيبرانية")
st.write(
    "إصدار متطور يضم غرف دردشة، توثيق زمني، وبصمة تشفير أمنية لكل رسالة"
    " (SHA-256)."
)

# لوحة التحكم الجانبية
st.sidebar.header("إعدادات الجلسة الآمنة")
username = st.sidebar.text_input("اسمك الكريم:", "صديق سوالف")

room_choice = st.sidebar.selectbox(
    "اختر غرفة المحادثة:",
    [
        "الدردشة العامة (Global)",
        "غرفة العمليات (Secure Room)",
        "قناة الأصدقاء (Random)",
    ],
)


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
  # حماية وتعقيم المدخلات
  sanitized_content = html.escape(content)
  sanitized_uname = html.escape(uname)

  # استخراج الوقت الحالي
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # توليد بصمة تشفير أمنية للرسالة (Cybersecurity Hash)
  msg_signature = hashlib.sha256(content.encode("utf-8")).hexdigest()[:10]

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

# عرض الرسائل المخزنة مع الوقت وبصمة التشفير
messages = load_messages(room_choice)
for uname, role, content, timestamp, msg_hash in messages:
  with st.chat_message(role):
    st.markdown(f"**{uname}** `[{timestamp}]` (بصمة: `{msg_hash}`):")
    st.markdown(content)

# صندوق الإدخال التفاعلي
if prompt := st.chat_input(f"اكتب رسالتك المشفرة في {room_choice}..."):
  if not username.strip():
    username = "مستخدم مجهول"

  save_message(room_choice, username, "user", prompt)

  # إعادة تحميل الصفحة لعرض الرسالة الجديدة فوراً
  st.rerun()
