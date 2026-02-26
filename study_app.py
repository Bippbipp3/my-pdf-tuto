import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. 기본 설정 ---
API_KEY = "AIzaSyBrhmxgYdKaBiVtfKCdD_wXgN4T0kSjrFI"
genai.configure(api_key=API_KEY)

# --- 2. 구글 시트 연결 (Secrets 사용) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. AI 모델 원칙 설정 ---
SYSTEM_INSTRUCTION = """
너는 PDF 학습 보조 AI다. 다음 '원칙'을 절대적으로 준수하라:
1. 철저한 폐쇄성: 오직 업로드한 PDF 내용으로만 답변할 것.
2. 출처 명시: 답변 시 해당 내용이 PDF의 몇 페이지에 있는지 언급할 것.
3. 모바일 최적화: 표는 가로 3칸 이내로 작성할 것.
"""

model = genai.GenerativeModel(
    model_name="gemini-flash-latest",
    system_instruction=SYSTEM_INSTRUCTION
)

# --- 4. 앱 UI 스타일 ---
st.set_page_config(page_title="PDF 학습 비서", layout="wide")
st.markdown("""
    <style>
    .stMarkdown table { display: block; overflow-x: auto; white-space: nowrap; }
    th, td { min-width: 150px; text-align: left; }
    .stButton>button { width: 100%; text-align: left; overflow: hidden; text-overflow: ellipsis; }
    </style>
    """, unsafe_allow_html=True)

st.title("📚 나만의 저장형 PDF 비서")

# --- 5. 데이터 불러오기 (앱 켤 때 실행) ---
if "chat_history" not in st.session_state:
    try:
        # 구글 시트에서 기존 데이터 읽어오기
        df = conn.read(worksheet="시트1")
        st.session_state.chat_history = []
        for _, row in df.iterrows():
            st.session_state.chat_history.append((row['Role'], row['Message']))
    except:
        st.session_state.chat_history = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# --- 6. 사이드바 (파일 업로드 & 질문 목록) ---
with st.sidebar:
    st.header("📂 학습 도구")
    uploaded_file = st.file_uploader("PDF 업로드", type="pdf")
    
    if uploaded_file:
        # PDF 텍스트 추출 (세션에 저장하여 반복 작업 방지)
        if st.session_state.pdf_text == "":
            reader = PdfReader(uploaded_file)
            st.session_state.pdf_text = "".join([p.extract_text() for p in reader.pages])
        st.success("PDF 로드 완료!")

    st.divider()
    st.subheader("📝 과거 질문 목록")
    # 질문만 추출해서 최근 10개 보여주기
    user_qs = [msg for role, msg in st.session_state.chat_history if role == "user"]
    for i, q in enumerate(user_qs[-10:]):
        if st.button(f"{i+1}. {q[:20]}...", key=f"q_{i}"):
            st.info(f"질문 내용: {q}")

# --- 7. 메인 대화창 표시 ---
for role, text in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)

# --- 8. 질문 처리 및 시트 저장 ---
if prompt := st.chat_input("질문을 입력하세요"):
    if not st.session_state.pdf_text:
        st.warning("PDF를 먼저 업로드해주세요!")
    else:
        # 사용자 질문 추가
        st.session_state.chat_history.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 답변 생성
        full_p = f"문서 내용: {st.session_state.pdf_text}\n\n질문: {prompt}"
        response = model.generate_content(full_p)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.chat_history.append(("assistant", response.text))

        # [핵심] 구글 시트에 실시간 업데이트
        try:
            # 전체 대화 기록을 데이터프레임으로 변환
            save_df = pd.DataFrame(st.session_state.chat_history, columns=['Role', 'Message'])
            save_df['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 시트에 덮어쓰기
            conn.update(worksheet="시트1", data=save_df)
        except Exception as e:
            st.error(f"저장 중 오류: {e}")
        
        st.rerun()

