import streamlit as st

st.set_page_config(page_title="منصة سوالف", page_icon="💬")
st.title("💬 منصة سوالف العراقية")

# تهيئة الرسائل والحالات
if "messages" not in st.session_state:
    st.session_state.messages = []

if "statuses" not in st.session_state:
    st.session_state.statuses = {}

# القائمة الجانبية لإعدادات المستخدم والحالة
st.sidebar.header("👤 ملفك الشخصي والحالة")
username = st.sidebar.text_input("اكتب اسمك هنا:", value="")
user_status = st.sidebar.text_input("حالتك / وقت تواجدك القادم:", value="متواجد حالياً أو سأدخل لاحقاً...")

# حفظ حالة المستخدم
if username:
    st.session_state.statuses[username] = user_status

# عرض حالات الأصدقاء والمتواجدين في القائمة الجانبية
if st.session_state.statuses:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 حالات الأصدقاء:")
    for user, status in st.session_state.statuses.items():
        st.sidebar.text(f"🔹 {user}:\n   {status}")

# واجهة الدردشة الرئيسية
st.markdown("---")
st.subheader("غرفة السوالف العامة")

# عرض رسائل الدردشة السابقة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(f"**{message['user']}**: {message['content']}")

# صندوق إرسال الرسائل
if username:
    if prompt := st.chat_input("اكتب رسالتك هنا..."):
        st.session_state.messages.append({"role": "user", "user": username, "content": prompt})
        st.rerun()
else:
    st.warning("⚠️ يرجى كتابة اسمك في القائمة الجانبية (Sidebar) فوق حتى تكدر تسولف وترسل رسائل.")
