import sqlite3
import streamlit as st

# مسار قاعدة البيانات في مجلد النظام المؤقت المسموح بالكتابة عليه
DB_PATH = "/tmp/sawalf.db"


def get_connection():
  return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
  try:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                role TEXT,
                content TEXT
            )
        """)
    conn.commit()
    conn.close()
  except Exception as e:
    st.error(f"خطأ في قاعدة البيانات: {e}")


init_db()

st.set_page_config(
    page_title="سوالف - Sawalf", page_icon="💬", layout="centered"
)

st.title("💬 تطبيق سوالف الاحترافي")
st.write(
    "هذا هو الإصدار المطور! الرسائل هنا لا تمسح أبداً بل تُحفظ في قاعدة بيانات"
    " حقيقية."
)

# لوحة جانبية لاختيار اسم المستخدم
st.sidebar.header("إعدادات الحساب")
username = st.sidebar.text_input("اسمك الكريم:", "صديق سوالف")


def load_messages():
  try:
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, role, content FROM messages")
    rows = c.fetchall()
    conn.close()
    return rows
  except Exception:
    return []


def save_message(uname, role, content):
  init_db()
  conn = get_connection()
  c = conn.cursor()
  c.execute(
      "INSERT INTO messages (username, role, content) VALUES (?, ?, ?)",
      (uname, role, content),
  )
  conn.commit()
  conn.close()


# عرض المحادثات القديمة المحفوظة
messages = load_messages()
for uname, role, content in messages:
  with st.chat_message(role):
    st.markdown(f"**{uname}**: {content}")

# صندوق الإدخال التفاعلي
if prompt := st.chat_input("اكتب رسالتك وسيتم حفظها بقاعدة البيانات..."):
  save_message(username, "user", prompt)
  with st.chat_message("user"):
    st.markdown(f"**{username}**: {prompt}")

  bot_response = f"يا هلا بيك يا {username}! رسالتك انحفظت وتوثقت بقاعدة البيانات بنجاح."
  save_message("نظام سوالف", "assistant", bot_response)
  with st.chat_message("assistant"):
    st.markdown(f"**نظام سوالف**: {bot_response}")
