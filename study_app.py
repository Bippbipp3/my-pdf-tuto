import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 설정 (AIzaSyBrhmxgYdKaBiVtfKCdD_wXgN4T0kSjrFI) ---
API_KEY = "AIzaSyBrhmxgYdKaBiVtfKCdD_wXgN4T0kSjrFI"
genai.configure(api_key=API_KEY)

# --- AI 모델 설정 (학습 원칙 고정) ---
SYSTEM_INSTRUCTION = """
너는 PDF 학습 보조 AI다. 다음 '원칙'을 절대적으로 준수하라:
1. 철저한 폐쇄성: 오직 업로드한 PDF 내용으로만 답변할 것. 외부 지식/웹 검색 절대 금지.
2. 출처 명시: 답변 시 해당 내용이 PDF의 몇 페이지에 있는지 언급할 것.
3. 모르면 솔직하게: PDF에 없는 내용이면 "문서 내에 해당 정보가 없습니다"라고 답할 것.
4. 요청별 맞춤 답변:
   - "요약해줘" -> 표나 불렛포인트로 한눈에 들어오게 정리.
   - "자세히" -> 문서의 세부 로직과 예시까지 포함하여 심층 설명.
"""

model = genai.GenerativeModel(
    model_name="gemini-flash-latest", # 속도가 빠른 모델
    system_instruction=SYSTEM_INSTRUCTION
)

# --- 앱 UI 만들기 ---
st.title("📚 나만의 PDF 학습 비서")
# --- 가로 스크롤 기능을 위한 스타일 설정 ---
st.markdown("""
    <style>
    /* 모든 표(table)에 가로 스크롤을 적용하고 글자 줄바꿈을 방지합니다 */
    .stMarkdown table {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }
    /* 표 내부 칸의 최소 너비를 지정하여 글자가 겹치지 않게 합니다 */
    th, td {
        min-width: 150px;
        text-align: left;
    }
    </style>
    """, unsafe_allow_html=True)

st.caption("업로드한 PDF 내용으로만 공부합니다.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

uploaded_file = st.sidebar.file_uploader("PDF 파일을 올려주세요", type="pdf")

if uploaded_file:
    # PDF 텍스트 추출
    reader = PdfReader(uploaded_file)
    pdf_text = ""
    for page in reader.pages:
        pdf_text += page.extract_text()
    
    st.sidebar.success("PDF 로드 완료!")

    # 대화창 표시
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(text)

    # 사용자 질문 입력
    if prompt := st.chat_input("PDF 내용에 대해 질문하세요"):
        st.session_state.chat_history.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 답변 생성
        full_prompt = f"문서 내용: {pdf_text}\n\n질문: {prompt}"
        response = model.generate_content(full_prompt)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)

            st.session_state.chat_history.append(("assistant", response.text))
