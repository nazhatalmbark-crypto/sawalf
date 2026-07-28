import hashlib
import html
from datetime import datetime, timedelta
import random
import sqlite3
import requests
import streamlit as st

# مسار قاعدة البيانات الموحد للموقع والبوت
DB_PATH = "sawalf_database.db"

# إعدادات بوت تليجرام (تم دمج التوكن الخاص بك هنا)
TELEGRAM_BOT_TOKEN = "8684721933:AAHouCzLPOoBd8n1_F9rNMaOXVcEJodCmaY"
TELEGRAM_CHAT_ID = (
    "ضع_الآيدي_الخاص_بك_هنا"  # استبدل هذه العبارة برقم الآيدي الخاص بك في تليجرام
)


def send_telegram_notification(message):
  if TELEGRAM_CHAT_ID != "ضع_الآيدي_الخاص_بك_هنا":
    try:
      url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
      requests.get(url, timeout=2)
    except Exception:
      pass


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
    c.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                username TEXT PRIMARY KEY,
                ban_type TEXT,
                unban_time TEXT,
                reason TEXT
            )
        """)
    c.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                username TEXT PRIMARY KEY,
                warn_count INTEGER
            )
        """)
    c.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter TEXT,
                reported_user TEXT,
                reason TEXT,
                timestamp TEXT
            )
        """)
    c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                gender TEXT,
                avatar TEXT,
                birth_month TEXT,
                birth_year TEXT,
                region TEXT,
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

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.username = ""


def check_and_cleanup_bans(uname):
  try:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT ban_type, unban_time FROM banned_users WHERE username = ?",
        (uname.lower(),),
    )
    row = c.fetchone()
    if row:
      b_type, u_time = row
      if b_type == "temp" and u_time:
        unban_dt = datetime.strptime(u_time, "%Y-%m-%d %H:%M:%S")
        if datetime.now() > unban_dt:
          c.execute(
              "DELETE FROM banned_users WHERE username = ?", (uname.lower(),)
          )
          c.execute("DELETE FROM warnings WHERE username = ?", (uname.lower(),))
          conn.commit()
          conn.close()
          return False
      conn.close()
      return True
    conn.close()
    return False
  except Exception:
    return False


# --- شاشة تسجيل الدخول والملف الشخصي ---
if not st.session_state.logged_in:
  st.title("🛡️ بوابة دخول منصة سوالف")
  st.write(
      "أهلاً بك! اختر اسمك، صورتك الرمزية (الأفاتار)، ومعلوماتك للبدء:"
  )

  with st.form("register_form"):
    input_username = st.text_input("اسم المستخدم الكريم:")
    input_gender = st.selectbox("الجنس:", ["ذكر 👦", "أنثى 👧"])
    input_avatar = st.selectbox(
        "اختر صورتك الرمزية (الأفاتار):",
        ["💻", "👨‍💻", "👩‍💻", "🚀", "🛡️", "🔥", "🦁", "🦊", "🐼", "⭐", "🦅"],
    )

    col1, col2 = st.columns(2)
    with col1:
      input_month = st.selectbox(
          "شهر الميلاد:",
          [
              "كانون الثاني",
              "شباط",
              "آذار",
              "نيسان",
              "آيار",
              "حزيران",
              "تموز",
              "آب",
              "أيلول",
              "تشرين الأول",
              "تشرين الثاني",
              "كانون الأول",
          ],
      )
    with col2:
      input_year = st.selectbox(
          "سنة الميلاد:",
          [str(y) for y in range(2015, 1970, -1)],
      )

    input_region = st.text_input("المنطقة / المحافظة (مثلاً: البصرة، بغداد...):")
    submit_button = st.form_submit_button(
        "دخول إلى المنصة 🚀", use_container_width=True
    )

    if submit_button:
      clean_name = input_username.strip()
      if not clean_name:
        st.error("⚠️ عذراً، يرجى كتابة اسم المستخدم أولاً!")
      elif check_and_cleanup_bans(clean_name):
        st.error("🚫 هذا الحساب محظور حالياً من قبل الإدارة!")
      else:
        try:
          current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          conn = get_connection()
          c = conn.cursor()
          c.execute(
              "INSERT OR REPLACE INTO users (username, gender, avatar,"
              " birth_month, birth_year, region, last_active) VALUES (?, ?,"
              " ?, ?, ?, ?, ?)",
              (
                  clean_name.lower(),
                  input_gender,
                  input_avatar,
                  input_month,
                  input_year,
                  input_region.strip() or "غير محدد",
                  current_time_str,
              ),
          )
          conn.commit()
          conn.close()

          st.session_state.logged_in = True
          st.session_state.username = clean_name
          st.success("🎉 تم تسجيل الدخول بنجاح!")
          st.rerun()
        except Exception as e:
          st.error(f"حدث خطأ: {e}")

  st.stop()

# --- التطبيق الرئيسي ---
username = st.session_state.username

if check_and_cleanup_bans(username):
  st.error(
      f"🚫 عذراً يا ({username})، تم حظر حسابك (بند) بسبب مخالفة القوانين."
  )
  if st.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()
  st.stop()


def get_user_avatar(uname):
  try:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT avatar FROM users WHERE username = ?", (uname.lower(),))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else "💬"
  except Exception:
    return "💬"


st.title("💬 تطبيق سوالف العراقية المطور")
st.sidebar.header(f"👤 الحساب: {username}")
if st.sidebar.button("تسجيل الخروج 🚪"):
  st.session_state.logged_in = False
  st.rerun()

room_options = [
    "الدردشة العامة (Global)",
    "غرفة البنات فقط 🌸",
    "غرفة الشباب فقط 🎮",
    "الدردشة المختلطة 🌐",
    "🔍 بحث عن شخص للخاص (حسب الجنس)",
    "🟢 الأعضاء المتواجدون حالياً",
    "🚨 الإبلاغ عن مستخدم",
    "📢 لوحة إعلانات المحظورين",
    "⚙️ لوحة إدارة المحظورين (الإدارة)",
]

room_choice = st.sidebar.selectbox("اختر القسم:", room_options)
actual_room = room_choice

# صفحة إعلانات المحظورين
if room_choice == "📢 لوحة إعلانات المحظورين":
  st.subheader("📢 لوحة إعلانات الحسابات المحظورة في المنصة")
  st.write(
      "هنا يتم عرض كافة الحسابات المحظورة، أسباب الحظر، والوقت المحدد لرفع البند"
      " عنها:"
  )


  def get_all_bans():
    try:
      conn = get_connection()
      c = conn.cursor()
      c.execute("SELECT username, ban_type, unban_time, reason FROM banned_users")
      rows = c.fetchall()
      conn.close()
      return rows
    except Exception:
      return []


  bans = get_all_bans()
  if not bans:
    st.success(
        "✅ سجل المنصة نظيف جداً! لا توجد أي حسابات محظورة حالياً."
    )
  else:
    for b_user, b_type, u_time, reason in bans:
      if b_type == "temp":
        ban_desc = f"حظر مؤقت (ينتهي في: `{u_time}`)"
      else:
        ban_desc = "حظر نهائي / دائم ⛔"
      st.error(
          f"👤 اسم الحساب: **{b_user}**\n* نوع الحظر: {ban_desc}\n* السبب:"
          f" `{reason}`"
      )
  st.stop()

# صفحة الإبلاغ عن مستخدم
elif room_choice == "🚨 الإبلاغ عن مستخدم":
  st.subheader("🚨 الإبلاغ عن مستخدم مسيء")
  st.write("إذا واجهت أي شخص يتجاوز أو يخالف القوانين، أبلغ عنه فوراً:")


  def get_all_other_users(current_u):
    try:
      conn = get_connection()
      c = conn.cursor()
      c.execute(
          "SELECT username FROM users WHERE username != ?", (current_u.lower(),)
      )
      rows = c.fetchall()
      conn.close()
      return [r[0] for r in rows]
    except Exception:
      return []


  other_users = get_all_other_users(username)
  if not other_users:
    st.info("لا توجد حسابات أخرى مسجلة لتقديم بلاغ ضدها.")
  else:
    with st.form("report_form"):
      reported_target = st.selectbox(
          "اختر اسم الشخص المخالف:", other_users
      )
      report_reason = st.text_area(
          "سبب البلاغ (تفاصيل التجاوز أو الإساءة):"
      )
      submit_report = st.form_submit_button("إرسال البلاغ للإدارة ⚠️")

      if submit_report:
        if not report_reason.strip():
          st.warning("يرجى كتابة سبب البلاغ أولاً.")
        else:
          try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = get_connection()
            c = conn.cursor()
            c.execute(
                "INSERT INTO reports (reporter, reported_user, reason,"
                " timestamp) VALUES (?, ?, ?, ?)",
                (username, reported_target, report_reason, current_time),
            )
            conn.commit()
            conn.close()
            st.success(
                "✅ تم إرسال بلاغك بنجاح، ستتم مراجعته من قبل البوت والإدارة!"
            )
            send_telegram_notification(
                f"🚨 بلاغ جديد من المنصة!\nالمبلغ: {username}\nالمخالف:"
                f" {reported_target}\nالسبب: {report_reason}"
            )
          except Exception as e:
            st.error(f"خطأ: {e}")
  st.stop()

elif room_choice == "🟢 الأعضاء المتواجدون حالياً":
  st.subheader("🟢 الأعضاء المسجلون في المنصة")


  def get_online_users():
    try:
      conn = get_connection()
      c = conn.cursor()
      c.execute("SELECT username, gender, avatar, birth_year, region FROM users")
      rows = c.fetchall()
      conn.close()
      return rows
    except Exception:
      return []


  for u_name, u_gender, u_avatar, u_year, u_region in get_online_users():
    st.markdown(
        f"{u_avatar} **{u_name}** | الجنس: {u_gender} | مواليد: `{u_year}` |"
        f" المنطقة: `{u_region}` 🟢 متصل"
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
  st.subheader("⚙️ لوحة تحكم الإدارة - فك الحظر عن الحسابات")


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
      c.execute("DELETE FROM warnings WHERE username = ?", (uname,))
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
            st.success(f"تم فك الحظر عن {b_user} بنجاح!")
            st.rerun()
  st.stop()

MILD_BAD_WORDS = ["غبي", "فاشل", "سخيف", "عبيط"]
STRONG_BAD_WORDS = ["حيوان", "زبالة", "ساقط", "كلب", "ندل", "حقير"]


def apply_ban(uname, ban_type, hours, reason):
  try:
    conn = get_connection()
    c = conn.cursor()
    if ban_type == "temp":
      unban_dt = datetime.now() + timedelta(hours=hours)
      unban_str = unban_dt.strftime("%Y-%m-%d %H:%M:%S")
      c.execute(
          "INSERT OR REPLACE INTO banned_users (username, ban_type, unban_time,"
          " reason) VALUES (?, ?, ?, ?)",
          (uname.lower(), "temp", unban_str, reason),
      )
    else:
      c.execute(
          "INSERT OR REPLACE INTO banned_users (username, ban_type, unban_time,"
          " reason) VALUES (?, ?, NULL, ?)",
          (uname.lower(), "permanent", reason),
      )
    conn.commit()
    conn.close()
  except Exception:
    pass


def get_user_warnings(uname):
  try:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT warn_count FROM warnings WHERE username = ?", (uname.lower(),)
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0
  except Exception:
    return 0


def increment_user_warning(uname):
  current_w = get_user_warnings(uname) + 1
  try:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO warnings (username, warn_count) VALUES (?, ?)",
        (uname.lower(), current_w),
    )
    conn.commit()
    conn.close()
  except Exception:
    pass
  return current_w


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
    user_avatar = get_user_avatar(uname) if role == "user" else "🤖"
    with st.chat_message(role, avatar=user_avatar):
      st.markdown(f"**{uname}** `[{timestamp}]`:")
      st.markdown(content)

  reply_to_user = st.text_input(
      "↩️ (اختياري) هل تريد الرد على شخص معين؟ اكتب اسمه هنا لتضمينه:"
  )

  if prompt := st.chat_input("اكتب رسالتك هنا..."):
    if actual_room == "DM_Waiting":
      st.error("يرجى اختيار شخص من قائمة البحث أولاً لبدء المحادثة!")
    else:
      final_content = prompt
      if reply_to_user.strip():
        final_content = f"*[رد على @{reply_to_user.strip()}]:* {prompt}"

      has_strong = any(w in prompt for w in STRONG_BAD_WORDS)
      has_mild = any(w in prompt for w in MILD_BAD_WORDS)

      save_message(actual_room, username, "user", final_content)

      if has_strong:
        apply_ban(
            username,
            "temp",
            24,
            "استخدام ألفاظ نابية وقوية جداً في المحادثة.",
        )
        alert_msg = f"🚨 تم حظر المستخدم ({username}) لمدة 24 ساعة بسبب استخدام كلمات قوية ومسيئة!"
        save_message(actual_room, "مدير النظام", "assistant", alert_msg)
        send_telegram_notification(
            f"⚠️ حظر قوي من الموقع!\nالمستخدم: {username}\nالسبب: {prompt}"
        )
        st.rerun()

      elif has_mild:
        warns = increment_user_warning(username)
        if warns == 1:
          alert_msg = f"⚠️ تنبيه إداري إلى ({username}): تم رصد لفظ غير لائق! هذا تحذيرك الأول، التزم بالآداب لئلا يتم بندك."
          save_message(actual_room, "مدير النظام", "assistant", alert_msg)
        else:
          apply_ban(
              username,
              "temp",
              2,
              "تكرار التجاوز بألفاظ مسيئة بعد التحذير.",
          )
          alert_msg = f"🚨 تم حظر المستخدم ({username}) لمدة ساعتين بسبب تكرار التجاوز رغم التحذير!"
          save_message(actual_room, "مدير النظام", "assistant", alert_msg)
          send_telegram_notification(
              f"⚠️ حظر مؤقت (ساعتين)!\nالمستخدم: {username}\nالسبب: تكرار"
              f" التجاوز"
          )
        st.rerun()

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
