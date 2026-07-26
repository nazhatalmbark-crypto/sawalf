import streamlit as st

st.set_page_config(page_title="سوالف - Sawalf", page_icon="💬", layout="centered")

st.title("💬 تطبيق سوالف")
st.write("أهلاً بك في مساحتك الخاصة للدردشة العشوائية والسوالف الحرة.")

# تهيئة سجل المحادثة داخل الجلسة
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض الرسائل القديمة عند تحديث الصفحة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# صندوق إدخال الرسائل من المستخدم
if prompt := st.chat_input("اكتب رسالتك هنا..."):
    # إضافة رسالة المستخدم للسجل
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # الرد التلقائي أو محاكاة البحث عن شخص للدردشة
    response = f"أهلاً بك! تم إرسال رسالتك بنجاح: '{prompt}'. جارٍ مطابقتك مع شخص آخر..."
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)