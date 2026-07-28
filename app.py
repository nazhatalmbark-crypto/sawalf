import hashlib
import html
from datetime import datetime, timedelta
import random
import sqlite3
import streamlit as st

DB_PATH = "/tmp/sawalf_pro_v9.db"


def get_connection():
  return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
  try:
    conn = get_connection()
    c = conn.cursor()
    # جدول الرسائل
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
    # جدول الحسابات المحظورة
    c.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                username TEXT PRIMARY KEY
            )
        """)
    # جدول المستخدمين مع تتبع وقت آخر ظهور (للمتواجدين)
    c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                gender TEXT,
                last_active TEXT
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

st.title("💬 تطبيق سوالف - مع نظام المتواجدين حالياً")
st.write(
    "دردشة حية، غرف متعددة، محادثات خاصة، بحث حسب الجنس، ومعرفة الأعضاء"
    " المتواجدين بالمنصة!"
)

# لوحة التحكم الجانبية
st.sidebar.header("إعدادات الجلسة والملف الشخصي")
username = st.sidebar.text_input("اسمك الكريم:", "صديق سوالف")
user_gender = st.sidebar.selectbox("جنسك:", ["ذكر 👦", "أنثى 👧"])

# تحديث بيانات المستخدم ووقت الظهور الحالي
if username.strip():
  try:
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO users (username, gender, last_active) VALUES"
        " (?, ?, ?)",
        (username.strip().lower(), user_gender, current_time_str),
    )
    conn.commit()
    conn.close()
  except Exception:
    pass


# التحقق من الحظر
def check_is_banned(uname):
  try:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM banned_users WHERE username = ?", (uname.lower(),))
    res = c.fetchone()
    conn.close()
    return res is not None
  except Exception:
    return False


if username.strip() and check_is_banned(username):
  st.error(f"🚫 عذراً يا ({username})، تم حظر حسابك من قبل الإدارة.")
  st.stop()

room_options = [
    "الدردشة العامة (Global)",
    "غرفة البنات فقط 🌸",
    "غرفة الشباب فقط 🎮",
    "الدردشة المختلطة 🌐",
    "🔍 بحث عن شخص للخاص (حسب الجنس)",
    "🟢 الأعضاء المتواجدون حالياً",
    "⚙️ لوحة إدارة المحظورين (الإدارة)",
]

room_choice = st.sidebar.selectbox("اختر القسم:", room_options)

actual_room = room_choice

# إذا اختار عرض الأعضاء المتواجدين
if room_choice == "🟢 الأعضاء المتواجدون حالياً":
  st.subheader("🟢 الأعضاء النشطون في المنصة مؤخراً")
  st.write("هذه قائمة بالأشخاص الذين فتحوا التطبيق وتفاعلوا معه:")


  def get_online_users():
    try:
      conn = get_connection()
      c = conn.cursor()
      # جلب المستخدمين الذين ظهروا خلال آخر 15 دقيقة مثلاً
      c.execute("SELECT username, gender, last_active FROM users")
      rows = c.fetchall()
      conn.close()
      return rows
    except Exception:
      return []


  online_users = get_online_users()
  if not online_users:
    st.info("لا توجد بيانات متاحة حالياً.")
  else:
    for u_name, u_gender, u_time in online_users:
      st.markdown(
          f"👤 **{u_name}** ({u_gender}) - آخر ظهور: `[{u_time}]` 🟢 متصل"
      )

  st.stop()

elif room_choice == "🔍 بحث عن شخص للخاص (حسب الجنس)":
  st.subheader("🔍 ابحث عن شخص وابدأ محادثة خاصة فوراً")
  target_gender = st.radio(
      "اختر الجنس المطلوب:", ["ذكر 👦", "أنثى 👧", "الكل 🌐"]
  )


  def get_users_by_gender(gender_filter, current_user):
    try:
      conn = get_connection()
      c = conn.cursor()
      if "الكل" in gender_filter:
        c.execute(
            "SELECT username, gender FROM users WHERE username != ?",
            (current_user.lower(),),
        )
      else:
        c.execute(
            "SELECT username, gender FROM users WHERE gender = ? AND username"
            " != ?",
            (gender_filter, current_user.lower()),
        )
      rows = c.fetchall()
      conn.close()
      return rows
    except Exception:
      return []


  found_users = get_users_by_gender(target_gender, username)

  if not found_users:
    st.info("📭 لا توجد حسابات مسجلة تطابق بحثك حالياً.")
    actual_room = "DM_Waiting"
  else:
    selected_target = st.selectbox(
        "اختر اسم الشخص لبدء المراسلة:", [r[0] for r in found_users]
    )
    if selected_target:
      users_sorted = sorted(
          [username.strip().lower(), selected_target.strip().lower()]
      )
      actual_room = f"DM_{users_sorted[0]}_{users_sorted[1]}"
      st.info(f"🔒 تم فتح محادثة خاصة مع العضو: {selected_target}")

elif room_choice == "⚙️ لوحة إدارة المحظورين (الإدارة)":
  st.subheader("⚙️ لوحة تحكم الإدارة - قائمة الحسابات المحظورة")


  def get_banned_list():
    try:
      conn = get_connection()
      c = conn.cursor()
      c.execute("SELECT username FROM banned_users")
      rows = c.fetchall()
      conn.close()
      return [r[0] for r in rows]
    except Exception:
      return []


  def unban_user(uname):
    try:
      conn = get_connection()
      c = conn.cursor()
      c.execute("DELETE FROM banned_users WHERE username = ?", (uname,))
      conn.commit()
      conn.close()
      return True
    except Exception:
      return False


  banned_list = get_banned_list()
  if not banned_list:
    st.success("✅ لا توجد أي حسابات محظورة حالياً.")
  else:
    for b_user in banned_list:
      col1, col2 = st.columns([3, 1])
      with col1:
        st.markdown(f"👤 **{b_user}**")
      with col2:
        if st.button(f"فك الحظر", key=f"unban_{b_user}"):
          if unban_user(b_user):
            st.success(f"تم فك الحظر عن {b_user}!")
            st.rerun()
  st.stop()

BAD_WORDS = ["حيوان", "غبي", "زبالة", "ساقط", "فاشل", "كلب"]


def ban_user(uname):
  try:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO banned_users (username) VALUES (?)",
        (uname.lower(),),
    )
    conn.commit()
    conn.close()
  except Exception:
    pass


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


if room_choice not in [
    "🔍 بحث عن شخص للخاص (حسب الجنس)",
    "🟢 الأعضاء المتواجدون حالياً",
]:
  st.subheader(f"📍 أنت الآن في: {room_choice}")
elif room_choice == "🔍 بحث عن شخص للخاص (حسب الجنس)":
  st.subheader("💬 نافذة المحادثة الخاصة")

if room_choice not in [
    "🟢 الأعضاء المتواجدون حالياً",
    "⚙️ لوحة إدارة المحظورين (الإدارة)",
]:
  messages = load_messages(actual_room)
  for uname, role, content, timestamp, msg_hash in messages:
    with st.chat_message(role):
      st.markdown(f"**{uname}** `[{timestamp}]`:")
      st.markdown(content)

  if prompt := st.chat_input("اكتب رسالتك هنا..."):
    if not username.strip():
      username = "مستخدم مجهول"

    if actual_room == "DM_Waiting":
      st.error("يرجى اختيار شخص من قائمة البحث أولاً لبدء المحادثة!")
    else:
      is_bad = False
      for word in BAD_WORDS:
        if word in prompt:
          is_bad = True
          break

      save_message(actual_room, username, "user", prompt)

      if is_bad:
        ban_user(username)
        alert_msg = (
            f"🚨 تم حظر الحساب ({username}) نهائياً بسبب استخدام كلمات مسيئة!"
        )
        save_message(actual_room, "مدير النظام", "assistant", alert_msg)
      elif "DM_" not in actual_room:
        user_text = prompt.lower()
        if "السلام عليكم" in user_text or "سلام عليكم" in user_text:
          bot_reply = (
              f"وعليكم السلام ورحمة الله وبركاته يا هلا بيك يا {username}!"
          )
        elif "هلو" in user_text or "هلا" in user_text:
          bot_reply = f"هلا بيك وبكل اهلنا يا {username}! منور المكان."
        else:
          general_replies = [
              f"افتهمت قصدك يا {username}، كمل وياي شنو عندك بعد؟",
              f"حلو كلش يا {username}، تسلم على هالمشاركة.",
          ]
          bot_reply = random.choice(general_replies)
        save_message(actual_room, "مساعد سوالف", "assistant", bot_reply)

      st.rerun()
