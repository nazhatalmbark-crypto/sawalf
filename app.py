import hashlib
import html
from datetime import datetime
import random
import sqlite3
import streamlit as st

# مسار قاعدة البيانات
DB_PATH = "/tmp/sawalf_pro_v3.db"


def get_connection():
  return sqlite3.connect(DB_PATH, check_same_thread=False)


# تهيئة قاعدة البيانات
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
    page_title="منصة سوالف التفاعلية", page_icon="💬", layout="centered"
)

st.title("💬 منصة سوالف العراقية")
st.write(
    "دردشة حية، غرف متعددة، ردود بشرية طبيعية، ونظام حماية ومراقبة للمتربصين"
    " بالعام!"
)

# لوحة التحكم الجانبية
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

# قائمة الكلمات الممنوعة لمراقبة الدردشة العامة
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

# عرض الرسائل المخزنة
messages = load_messages(room_choice)
for uname, role, content, timestamp, msg_hash in messages:
  with st.chat_message(role):
    st.markdown(f"**{uname}** `[{timestamp}]`:")
    st.markdown(content)

# صندوق الإدخال التفاعلي
if prompt := st.chat_input(f"اكتب رسالتك في {room_choice}..."):
  if not username.strip():
    username = "مستخدم مجهول"

  # فحص الغرفة العامة إذا بيها تجاوز أو كلمات مسيئة
  is_bad = False
  if "العامة" in room_choice:
    for word in BAD_WORDS:
      if word in prompt:
        is_bad = True
        break

  # حفظ رسالة المستخدم الأصلية
  save_message(room_choice, username, "user", prompt)

  # إذا الشخص غلط بالعامة، البوت يتدخل ويفضحه ويعطيه إنذار
  if is_bad:
    warning_responses = [
      f"⚠️ عذراً يا {username}، الألفاظ النابية ممنوعة هنا احترم الموجودين!",
      (
          f"🛑 يابو الهلا يا {username}, مو هج الأخلاق بالسوالف، اعدل كلامك"
          " لو سمحت!"
      ),
      (
          f"🚨 تنبيه إداري موجه إلى ({username}): تم رصد تجاوز، يرجى الالتزام"
          " بالآداب العامة."
      ),
    ]
    alert_msg = random.choice(warning_responses)
    save_message(room_choice, "مدير النظام", "assistant", alert_msg)
  else:
    # ردود بشرية طبيعية ومنوعة من البوت
    human_replies = [
      f"هلا بيك يا {username}، عاش من شافك! شلونك اليوم؟",
      f"صحيح كلامك يا {username}، فكرة كلش حلوة ومرتبة.",
      f"هههههه أي والله صدك يا {username}، دمت منور السوالف!",
      f"حبيبي يا {username}، منورنا والله، شنو رأيك بباقي الغرف؟",
      f"وصلت رسالتك يا ورد، تسلم على هالكلام الطيب.",
    ]
    bot_reply = random.choice(human_replies)
    save_message(room_choice, "مساعد سوالف", "assistant", bot_reply)

  st.rerun()
