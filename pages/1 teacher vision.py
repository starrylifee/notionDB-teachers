import streamlit as st
from openai import OpenAI
import requests
from datetime import datetime
import pathlib
import toml

# 페이지 설정 - 아이콘과 제목 설정
st.set_page_config(
    page_title="교사용 교육 도구 비전",  # 브라우저 탭에 표시될 제목
    page_icon="🧑‍🏫",  # 브라우저 탭에 표시될 아이콘 (이모지 또는 이미지 파일 경로)
)

# Streamlit의 배경색 변경
background_color = "#E0FFFF"

# 배경색 변경을 위한 CSS
page_bg_css = f"""
<style>
    .stApp {{
        background-color: {background_color};
    }}
</style>
"""

# Streamlit의 기본 메뉴와 푸터 숨기기
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden; }
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        var mainMenu = document.getElementById('MainMenu');
        if (mainMenu) {
            mainMenu.style.display = 'none';
        }
        var footer = document.getElementsByTagName('footer')[0];
        if (footer) {
            footer.style.display = 'none';
        }
        var header = document.getElementsByTagName('header')[0];
        if (header) {
            header.style.display = 'none';
        }
    });
    </script>
"""

# Streamlit에서 HTML 및 CSS 적용
st.markdown(hide_menu_style, unsafe_allow_html=True)
st.markdown(page_bg_css, unsafe_allow_html=True)

# secrets.toml 파일 경로
secrets_path = pathlib.Path(__file__).parent.parent / ".streamlit/secrets.toml"

# secrets.toml 파일 읽기
try:
    with open(secrets_path, "r") as f:
        secrets = toml.load(f)
except Exception as e:
    st.error(f"❌ secrets.toml 파일을 로드하는 중 오류가 발생했습니다: {e}")
    st.stop()

# OpenAI API 클라이언트 초기화
try:
    client = OpenAI(api_key=secrets["api"]["keys"][0])
except Exception as e:
    st.error(f"❌ OpenAI 클라이언트 초기화 중 오류가 발생했습니다: {e}")
    st.stop()

# Notion API 설정
NOTION_API_KEY = secrets["notion"]["api_key"]
NOTION_DATABASE_ID = secrets["notion"]["database_id"]
NOTION_API_URL = f"https://api.notion.com/v1/pages"

# Notion에서 활동 코드 중복 확인
def is_activity_code_duplicate(activity_code):
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "filter": {
            "property": "setting_name",
            "title": {
                "equals": activity_code
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            results = response.json().get("results")
            return len(results) > 0
        else:
            st.error(f"❌ Notion API 요청이 실패했습니다. 상태 코드: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"❌ Notion API 요청 중 오류가 발생했습니다: {e}")
        return False

# Notion에 데이터 저장
def save_to_notion(activity_code, final_prompt, email, password):
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "setting_name": {
                "rich_text": [{"text": {"content": activity_code}}]  # 활동 코드를 'rich_text'로 저장
            },
            "prompt": {
                "rich_text": [{"text": {"content": final_prompt}}]  # 프롬프트를 'rich_text'로 저장
            },
            "email": {
                "rich_text": [{"text": {"content": email}}]  # 이메일을 'rich_text'로 저장
            },
            "password": {
                "rich_text": [{"text": {"content": password}}]  # 비밀번호를 'rich_text'로 저장
            },
            "date": {
                "title": [{"text": {"content": datetime.now().isoformat()}}]  # 생성 시간을 'title'로 저장
            },
            "page": {
                "rich_text": [{"text": {"content": "vision"}}]  # 페이지 필드를 'rich_text'로 저장
            }
        }
    }

    try:
        response = requests.post(NOTION_API_URL, headers=headers, json=data)
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ Notion 데이터 저장 중 오류가 발생했습니다: {e}")
        return False

# 교사용 인터페이스
st.title("🎓 교사용 이미지 분석 프롬프트 생성 도구")

st.markdown("""
**안내:** 이 도구를 사용하여 이미지 분석 API를 활용한 교육용 프롬프트를 쉽게 생성할 수 있습니다. 다음 중 하나의 방법을 선택하세요:
1. **샘플 프롬프트 이용하기**: 미리 준비된 샘플 프롬프트를 사용해 보세요.
2. **직접 프롬프트 만들기**: 프롬프트를 직접 작성하세요.
3. **인공지능 도움받기**: 인공지능의 도움을 받아 프롬프트를 생성하세요.
4. **학생용 앱과 연동**: 이곳에서 저장한 프롬프트는 [학생용 앱](https://students-ai.streamlit.app/)에서 불러와 안전하게 AI를 사용할 수 있습니다.
""")

# 샘플 프롬프트 목록
sample_prompts = {
    "사진 속 감정 분석": "사진 속 인물들의 감정을 분석하여 초등학생이 이해할 수 있도록 설명해 주세요.",
    "풍경 사진 설명": "풍경 사진을 보고, 그 특징과 아름다움을 초등학생이 이해할 수 있도록 설명해 주세요.",
    "동물 사진 설명": "동물 사진을 보고, 그 동물의 특성을 설명하고, 초등학생이 이해할 수 있도록 쉽게 풀어 설명해 주세요.",
    "미술 작품 분석": "미술 작품 사진을 보고, 초등학생이 이해할 수 있도록 그 작품의 주요 특징을 설명해 주세요.",
}

# 프롬프트 생성 방법 선택
prompt_method = st.selectbox("프롬프트 생성 방법을 선택하세요:", ["샘플 프롬프트 이용하기", "직접 입력", "인공지능 도움 받기"])

# 세션 상태 초기화
if "direct_prompt" not in st.session_state:
    st.session_state.direct_prompt = ""
if "ai_prompt" not in st.session_state:
    st.session_state.ai_prompt = ""
if "final_prompt" not in st.session_state:
    st.session_state.final_prompt = ""

# 샘플 프롬프트 이용하기
if prompt_method == "샘플 프롬프트 이용하기":
    st.subheader("📚 샘플 프롬프트")
    selected_sample = st.selectbox("샘플 프롬프트를 선택하세요:", ["선택하세요"] + list(sample_prompts.keys()))

    if selected_sample != "선택하세요":
        st.session_state.direct_prompt = st.text_area("✏️ 샘플 프롬프트 수정 가능:", value=sample_prompts[selected_sample], height=300)
        st.session_state.final_prompt = st.session_state.direct_prompt

# 직접 프롬프트 입력
elif prompt_method == "직접 입력":
    example_prompt = "예시: 너는 A활동을 돕는 보조교사 입니다. 학생이 B사진을 입력하면, 인공지능이 B를 분석하여 C를 할 수 있도록 도움을 주세요."
    st.session_state.direct_prompt = st.text_area("✏️ 직접 입력할 프롬프트:", example_prompt, height=300)
    st.session_state.final_prompt = st.session_state.direct_prompt

# 인공지능 도움 받기
elif prompt_method == "인공지능 도움 받기":
    input_topic = st.text_input("📚 프롬프트 주제 또는 키워드를 입력하세요:", "")

    if st.button("✨ 인공지능아 프롬프트를 만들어줘"):
        if input_topic.strip() == "":
            st.error("⚠️ 주제를 입력하세요.")
        else:
            with st.spinner('🧠 프롬프트를 생성 중입니다...'):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",  # 적절한 GPT 모델을 선택
                        messages=[
                            {"role": "system", "content": "당신은 Vision API를 사용하여 교육 목적으로 시스템 프롬프트를 만드는 것을 돕는 AI입니다. 이미지의 시각적 요소를 분석하여 이에 기반한 프롬프트를 생성하세요."},
                            {"role": "user", "content": f"프롬프트의 주제는: {input_topic}입니다. 이 주제를 바탕으로 Vision API를 사용하여 창의적이고 교육적인 시스템 프롬프트를 생성해 주세요."}
                        ]
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        st.session_state.ai_prompt = response.choices[0].message.content.strip()
                        st.session_state.final_prompt = st.session_state.ai_prompt  # 최종 프롬프트 업데이트
                    else:
                        st.error("⚠️ 프롬프트 생성에 실패했습니다. 다시 시도해 주세요.")
                        st.session_state.ai_prompt = ""

                except Exception as e:
                    st.error(f"⚠️ 프롬프트 생성 중 오류가 발생했습니다: {e}")
                    st.session_state.ai_prompt = ""

    # 인공지능 프롬프트가 생성된 경우에만 표시
    if st.session_state.ai_prompt:
        st.session_state.ai_prompt = st.text_area("✏️ 인공지능이 만든 프롬프트를 살펴보고 직접 수정하세요:", 
                                                  value=st.session_state.ai_prompt, height=300)
        st.session_state.final_prompt = st.session_state.ai_prompt

# 활동 코드 입력
if st.session_state.final_prompt:
    st.subheader("🔑 활동 코드 설정")
    activity_code = st.text_input("활동 코드를 입력하세요", value=st.session_state.get('activity_code', '')).strip()

    # 숫자만 입력된 경우에도 허용하도록 변경
    if activity_code and is_activity_code_duplicate(activity_code):
        st.error("⚠️ 이미 사용된 코드입니다. 다른 코드를 입력해주세요.")
        activity_code = ""  # 중복된 경우 초기화
    else:
        st.session_state['activity_code'] = activity_code

    # Email 및 Password 입력
    email = st.text_input("📧 Email (선택사항) 학생의 생성결과물을 받아볼 수 있습니다.", value=st.session_state.get('email', '')).strip()
    password = st.text_input("🔒 Password (선택사항) 저장한 프롬프트를 조회, 삭제할 수 있습니다.", value=st.session_state.get('password', ''), type="password").strip()

    st.markdown("**[https://students-ai.streamlit.app/](https://students-ai.streamlit.app/)** 에서 학생들이 이 활동 코드를 입력하면 해당 프롬프트를 불러올 수 있습니다.")

# 서버 저장 버튼은 항상 표시되며, 입력 검증 후 동작
if st.button("💾 프롬프트를 서버에 저장"):
    if not st.session_state.final_prompt.strip():
        st.error("⚠️ 프롬프트가 없습니다. 먼저 프롬프트를 생성하세요.")
    elif not activity_code:
        st.error("⚠️ 활동 코드를 입력하세요.")
    elif password and password.isnumeric():
        st.error("⚠️ 비밀번호는 숫자만 입력할 수 없습니다. 영문 또는 영문+숫자 조합을 사용하세요.")
    else:
        with st.spinner('💾 데이터를 저장하는 중입니다...'):
            if save_to_notion(activity_code, st.session_state.final_prompt, email, password):
                st.success(f"🎉 프롬프트가 성공적으로 저장되었습니다. **저장된 값:**\n\n**활동 코드:** {activity_code}\n**프롬프트:** {st.session_state.final_prompt}")
            else:
                st.error("❌ 프롬프트 저장 중 오류가 발생했습니다.")
