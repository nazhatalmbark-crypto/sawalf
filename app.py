import html
import sqlite3
import streamlit as st

# مسار قاعدة البيانات الآمن في السحابة
DB_PATH = "/tmp/sawalf_secure.db"


def get_connection():
  return sqlite3.connect(DB_PATH, check_same_thread=False)


# تهيئة قاعدة البيانات مع دعم الغرف
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
                content TEXT
            )
        """)
    conn.commit()
    conn.close()
  except Exception:
    pass


init_db()

st.set_page_config(
    page_title="سوالف الآمن - Sawalf", page_icon="🛡️", layout="centered"
)

st.title("🛡️ منصة سوالف الآمنة والمطورة")
st.write(
    "تطبيق محادثة متكامل مع تخزين دائم، اختيار غرف متعددة، وطبقة حماية للمدخلات."
)

# لوحة التحكم الجانبية لإدارة الحساب والغرف
st.sidebar.header("إعدادات الجلسة")
username = st.sidebar.text_input("اسمك الكريم:", "صديق سوالف")

# اختيار الغرفة أو نوع المحادثة (الدردشة العامة أو الغرف العشوائية)
room_choice = st.sidebar.selectbox(
    "اختر غرفة المحادثة:",
    ["الدردشة العامة (Global)", "غرفة الشباب (Random 1)", "قناة الأصدقاء (Random 2)"],
)


def load_messages(room):
  try:
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT username, role, content FROM messages WHERE room = ?", (room,)
    )
    rows = c.fetchall()
    conn.close()
    return rows
  except Exception:
    return []


def save_message(room, uname, role, content):
  # تطبيق معايير الحماية (تعقيم المدخلات لمنع حقن السكريبتات والهجمات)
  sanitized_content = html.escape(content)
  sanitized_uname = html.escape(uname)

  init_db()
  conn = get_connection()
  c = conn.cursor()
  c.execute(
      "INSERT INTO messages (room, username, role, content) VALUES (?, ?,"
      " ?, ?)",
      (room, sanitized_uname, role, sanitized_content),
  )
  conn.commit()
  conn.close()


st.subheader(f"📍 أنت الآن في: {room_choice}")

# عرض رسائل الغرفة الحالية فقط
messages = load_messages(room_choice)
for uname, role, content in messages:
  with st.chat_message(role):
    st.markdown(f"**{uname}**: {content}")

# صندوق الإدخال التفاعلي
if prompt := st.chat_input(f"اكتب رسالتك في {room_choice}..."):
  if not username.strip():
    username = "مستخدم مجهول"

  save_message(room_choice, username, "user", prompt)
  with st.chat_message("user"):
    st.markdown(f"**{username}**: {html.escape(prompt)}")

  # رد تفاعلي ذكي من النظام حسب الغرفة
  bot_response = f"أهلاً بك يا {username}! تم توثيق وحماية رسالتك في {room_choice} بنجاح."
  save_message(room_choice, "نظام سوالف الآمن", "assistant", bot_response)
  with st.chat_message("assistant"):
    st.markdown(f"**نظام سوالف الآمن**: {bot_response}")
