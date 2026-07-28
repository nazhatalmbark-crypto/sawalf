import streamlit as st
import requests

# إعدادات الصفحة
st.set_page_config(page_title="منصة سوالف العراقية", page_icon="💬", layout="centered")

# إعدادات بوت التليجرام (ضع التوكن والآيدي الخاص بك هنا)
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # استبدله بتوكن البوت الخاص بك
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"      # استبدله برقم الـ Chat ID الخاص بك

def send_telegram_notification(sender_name, message_text):
    if TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" and TELEGRAM_CHAT_ID != "YOUR_CHAT_ID_HERE":
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"🔔 رسالة جديدة بالموقع من: {sender_name}\n💬 النص: {message_text}"
            }
            requests.post(url, json=payload, timeout=2)
        except Exception:
            pass

# دالة البوت المحذر (لفحص الرسائل وحظر الكلمات غير اللائقة)
def check_moderation(text):
    bad_words = ["كلمة_مسيئة_1", "كلمة_مسيئة_2"] # تقدر تضيف الكلمات اللي تحذر منها
    for word in bad_words:
        if word in text:
            return False, "⚠️ تنبيه من بوت الحماية: تم رصد كلمة غير لائقة، يرجى الالتزام بالآداب العامة!"
    return True, ""

# تهيئة مخزن الرسائل والحالات
if "messages" not in st.session_state:
    st.session_state.messages = []
if "statuses" not in st.session_state:
    st.session_state.statuses = {}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- واجهة تسجيل الدخول (البوابة) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🇮🇶 بوابة دخول منصة سوالف</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input("👤 اكتب اسمك الحلو هنا:", placeholder="مثلاً: حمودي البغدادي")
        status = st.text_input("📌 حالتك أو شوكت تتواجد؟", placeholder="مثلاً: موجود لليل / مشغول حالياً")
        
        if st.button("🚀 دخول للمنصة"):
            if name:
                st.session_state.user_name = name
                st.session_state.statuses[name] = status if status else "متواجد حالياً"
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("لازم تكتب اسمك حتى أصدقائك يعرفونك!")

# --- واجهة الدردشة الرئيسية (تظهر بعد الدخول) ---
else:
    st.title(f"💬 هلا بيك يا {st.session_state.user_name}")
    
    # القائمة الجانبية لعرض الحالات (Sidebar)
    st.sidebar.header("📌 تواجد الأصدقاء")
    for user, user_st in st.session_state.statuses.items():
        st.sidebar.markdown(f"**🔹 {user}**")
        st.sidebar.caption(f"{user_st}")
        st.sidebar.write("---")

    # عرض الرسائل
    st.markdown("---")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"**{message['user']}**: {message['content']}")

    # صندوق الإرسال
    if prompt := st.chat_input("اكتب رسالتك وسولف وياهم..."):
        # فحص الحماية والتحذير
        is_allowed, warning_msg = check_moderation(prompt)
        if not is_allowed:
            st.warning(warning_msg)
        else:
            # حفظ الرسالة وإرسال إشعار التليجرام
            st.session_state.messages.append({"role": "user", "user": st.session_state.user_name, "content": prompt})
            send_telegram_notification(st.session_state.user_name, prompt)
            st.rerun()

    # زر الخروج
    if st.sidebar.button("🚪 تسجيل خروج"):
        st.session_state.logged_in = False
        st.rerun()
