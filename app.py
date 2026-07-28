import streamlit as st
import requests

# إعدادات الصفحة
st.set_page_config(page_title="منصة سوالف العراقية", page_icon="💬", layout="centered")

# إعدادات بوت التليجرام
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

# تهيئة المخزن
if "messages" not in st.session_state:
    st.session_state.messages = []
if "users_data" not in st.session_state:
    st.session_state.users_data = {}  # يحفظ بيانات كل مستخدم (صورة، محافظة، جنس، حالة)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- واجهة تسجيل الدخول (البوابة الرئيسية) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🇮🇶 بوابة دخول منصة سوالف</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input("👤 اكتب اسمك الحلو هنا:", placeholder="مثلاً: حمودي البغدادي")
        status = st.text_input("📌 حالتك أو شوكت تتواجد؟", placeholder="مثلاً: موجود لليل / مشغول حالياً")
        
        # اختيار الجنس والمحافظة
        gender = st.selectbox("🚻 الجنس:", ["ذكر", "أنثى"])
        governorate = st.selectbox("🏙️ المحافظة:", [
            "بغداد", "البصرة", "نينوى", "أربيل", "السليمانية", "كركوك", "النجف", "كربلاء", 
            "بابل", "الأنبار", "ديالى", "ذي قار", "ميسان", "المثنى", "القادسية", "واسط", "صلاح الدين", "دهوك"
        ])
        
        # رفع الصورة الشخصية من المعرض
        profile_image = st.file_uploader("🖼️ اختر صورتك الشخصية من المعرض:", type=["jpg", "png", "jpeg"])
        
        if st.button("🚀 دخول للمنصة"):
            if name:
                st.session_state.user_name = name
                st.session_state.users_data[name] = {
                    "status": status if status else "متواجد حالياً",
                    "gender": gender,
                    "governorate": governorate,
                    "avatar": profile_image
                }
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("لازم تكتب اسمك حتى أصدقائك يعرفونك!")

# --- واجهة الدردشة الرئيسية (تظهر بعد الدخول) ---
else:
    current_user = st.session_state.user_name
    current_data = st.session_state.users_data.get(current_user, {})
    
    st.title(f"💬 هلا بيك يا {current_user}")
    
    # القائمة الجانبية لعرض تفاصيل وحالات الأصدقاء مع صورهم
    st.sidebar.header("📌 الأصدقاء والمتواجدون")
    for usr, data in st.session_state.users_data.items():
        sb_col1, sb_col2 = st.sidebar.columns([1, 3])
        with sb_col1:
            if data.get("avatar"):
                st.image(data["avatar"], width=40)
            else:
                st.write("👤")
        with sb_col2:
            st.sidebar.markdown(f"**{usr}**")
            st.sidebar.caption(f"🏙️ {data.get('governorate')} | 🚻 {data.get('gender')}")
            st.sidebar.caption(f"📌 {data.get('status')}")
        st.sidebar.write("---")

    # عرض الرسائل
    st.markdown("---")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            sender = message["user"]
            s_data = st.session_state.users_data.get(sender, {})
            gov = s_data.get('governorate', '')
            gov_str = f" ({gov})" if gov else ""
            st.markdown(f"**{sender}**{gov_str}: {message['content']}")

    # صندوق الإرسال
    if prompt := st.chat_input("اكتب رسالتك وسولف وياهم..."):
        is_allowed, warning_msg = check_moderation(prompt)
        if not is_allowed:
            st.warning(warning_msg)
        else:
            st.session_state.messages.append({"role": "user", "user": current_user, "content": prompt})
            send_telegram_notification(current_user, prompt)
            st.rerun()

    # زر الخروج
    if st.sidebar.button("🚪 تسجيل خروج"):
        st.session_state.logged_in = False
        st.rerun()
