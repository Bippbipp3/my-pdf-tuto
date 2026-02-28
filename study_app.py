import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. API 키 설정 (본인의 API 키만 정확히 넣어주세요) ---
import streamlit as st
import google.generativeai as genai

# 직접 키를 적지 않고 st.secrets를 사용합니다.
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# --- 2. AI 모델 설정 ---
model = genai.GenerativeModel(
    model_name="gemini-flash-latest",
    system_instruction="너는 PDF 학습 보조 AI다. 업로드된 내용으로만 친절하게 답변해줘."
)

# --- 3. 앱 화면 구성 ---
st.set_page_config(page_title="PDF 학습 비서", layout="centered")
st.title("📚 심플 PDF 학습 비서")
st.caption("구글 시트 연결 없이 깔끔하게 대화만 가능합니다.")

# 대화 기록 및 PDF 텍스트 저장용 세션
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# --- 4. 사이드바 (PDF 업로드) ---
with st.sidebar:
    st.header("📂 파일 업로드")
    uploaded_file = st.file_uploader("PDF 파일을 올려주세요", type="pdf")
    
    if uploaded_file:
        # 새로운 파일이 올라오면 텍스트 추출
        reader = PdfReader(uploaded_file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
        st.session_state.pdf_text = full_text
        st.success("PDF 로드 완료!")
    
    if st.button("대화 초기화"):
        st.session_state.chat_history = []
        st.rerun()

# --- 5. 대화창 표시 ---
for role, text in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)

# --- 6. 질문 처리 ---
if prompt := st.chat_input("질문을 입력하세요"):
    if not st.session_state.pdf_text:
        st.warning("PDF를 먼저 업로드해주세요!")
    else:
        # 사용자 메시지 표시
        st.session_state.chat_history.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 답변 생성
        try:
            full_prompt = f"문서 내용: {st.session_state.pdf_text}\n\n질문: {prompt}"
            response = model.generate_content(full_prompt)
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.chat_history.append(("assistant", response.text))
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
