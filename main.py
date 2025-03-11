import streamlit as st
import os
import importlib.util
import base64

# 페이지 설정
st.set_page_config(page_title="Dashboard", page_icon="🔋", layout="wide")

# 🎨 배경 이미지 로드 함수 (확장자 png로 수정 완료!)
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded}"

# 페이지 선택 상태 관리
if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "🏠 Main"

# 🎯 사용자 정의 사이드바
st.sidebar.title("🚀 메뉴")
page_options = {
    "🏠 Main": "main",
    "🏢 Company": "1_company",
    "👥 Client": "2_client"
}
selected_page = st.sidebar.radio("📂 Select a Page:", list(page_options.keys()))
st.session_state["selected_page"] = selected_page

# 🖼️ 배경 이미지 적용 (메인 대시보드에서만 적용)
if selected_page == "🏠 Main":
    bg_image_path = "battery_.png"
    if os.path.exists(bg_image_path):
        bg_image = get_base64_image(bg_image_path)
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background: url("{bg_image}") no-repeat center center fixed;
                    background-size: cover;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

# 🎨 CSS를 활용하여 자동 생성 사이드바 숨기기
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        .stApp {
            padding-top: 10px;
        }
        section[data-testid="stSidebar"] {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
        }
        .stSidebar .st-bc {
            color: black;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 페이지 로드
if selected_page == "🏠 Main":
    st.markdown(
        """
        <h1 style="text-align: right; color: white;"> Welcome to the ✨Chill✨ Dashboard</h1>
        <p style="text-align: right; color: white;">
            <b>배터리 성능을 분석</b>하고 <b>기업과 고객에게 유용한 데이터를 제공</b>합니다.<br>
            <b>메뉴바</b>에서 원하는 페이지를 선택하여 데이터를 확인하세요.<br>
            데이터를 업로드하고 분석 결과를 시각적으로 확인할 수 있습니다.
        </p>
        """,
        unsafe_allow_html=True
    )

else:
    # 선택한 페이지 불러오기 함수
    def load_page(page_name):
        page_path = os.path.join("pages", f"{page_name}.py")
        if os.path.exists(page_path):
            spec = importlib.util.spec_from_file_location("module.name", page_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            st.error(f"🚨 '{page_name}.py' 파일을 찾을 수 없습니다.")
    # 기존 화면을 지우고 새로운 페이지만 표시
    st.empty()  # 기존 화면 비우기
    load_page(page_options[selected_page])

    


     





