import streamlit as st
import requests
from datetime import datetime
import pathlib
import toml

# 페이지 설정 - 아이콘과 제목 설정
st.set_page_config(
    page_title="교사용 교육 도구 이미지",  # 브라우저 탭에 표시될 제목
    page_icon="🧑‍🏫",  # 브라우저 탭에 표시될 아이콘 (이모지 또는 이미지 파일 경로)
)


# Streamlit의 배경색 변경
background_color = "#FFEBEE"

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
with open(secrets_path, "r") as f:
    secrets = toml.load(f)

# Notion API 설정
NOTION_API_KEY = secrets["notion"]["api_key"]
NOTION_DATABASE_ID = secrets["notion"]["database_id"]
NOTION_API_URL = f"https://api.notion.com/v1/pages"

# Notion에서 활동 코드 중복 확인 (page가 'image'일 경우에만 중복 확인)
def is_activity_code_duplicate_for_image(activity_code):
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "filter": {
            "and": [
                {
                    "property": "page",
                    "rich_text": {
                        "equals": "image"
                    }
                },
                {
                    "property": "setting_name",  # '활동 코드' 속성 대신 실제 데이터베이스 속성 이름 사용
                    "rich_text": {
                        "equals": activity_code
                    }
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        results = response.json().get("results")
        return len(results) > 0
    else:
        st.error(f"⚠️ Notion API 호출 실패: {response.status_code} - {response.text}")
        return False

# Notion에 데이터 저장
def save_to_notion(activity_code, input_topic, email, password):
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
                "rich_text": [{"text": {"content": input_topic}}]  # 프롬프트를 'rich_text'로 저장
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
                "rich_text": [{"text": {"content": "image"}}]  # 페이지 필드를 'image'로 저장
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
st.title("🎨 교사용 이미지 생성 프롬프트 도구")

st.markdown("""
**안내:** 이 도구를 사용하여 교육 활동에 필요한 이미지 생성 프롬프트를 직접 입력하고 저장할 수 있습니다. 아래의 단계를 따라 입력해 주세요.
1. **활동 코드**: 학생들이 입력할 고유 코드를 설정합니다.
2. **이미지 대상**: 생성하고자 하는 이미지의 대상을 간단하게 입력합니다.
3. **프롬프트 저장**: 입력한 프롬프트를 저장하여 서버에 추가합니다.
4. **학생용 앱과 연동**: 이곳에서 저장한 프롬프트는 [학생용 앱](https://students.streamlit.app/)에서 불러와 안전하게 AI를 사용할 수 있습니다.
""")

# 활동 코드 입력 (중복 검사 및 오류 처리)
activity_code = st.text_input("🔑 활동 코드 입력", value=st.session_state.get('activity_code', '')).strip()

if is_activity_code_duplicate_for_image(activity_code):
    st.error("⚠️ 이미 사용된 코드입니다. 다른 코드를 입력해주세요.")
    activity_code = ""  # 중복된 경우 초기화
else:
    st.session_state['activity_code'] = activity_code

# 교사가 이미지 대상을 입력
input_topic = st.text_input("🖼️ 이미지 대상을 간단하게 입력하세요 (예: '곰', '나무', '산'): ", "")

# Email 및 Password 입력
email = st.text_input("📧 Email (선택사항) 학생의 생성결과물을 받아볼 수 있습니다.", value=st.session_state.get('email', '')).strip()
password = st.text_input("🔒 Password (선택사항) 저장한 프롬프트를 조회, 삭제할 수 있습니다.", value=st.session_state.get('password', ''), type="password").strip()

# 프롬프트 바로 저장
if st.button("💾 프롬프트를 서버에 저장") and activity_code:
    if input_topic:
        if password and password.isnumeric():
            st.error("⚠️ 비밀번호는 숫자만 입력할 수 없습니다. 영문 또는 영문+숫자 조합을 사용하세요.")
        else:
            with st.spinner('💾 데이터를 저장하는 중입니다...'):
                if save_to_notion(activity_code, input_topic, email, password):
                    st.success("🎉 프롬프트가 성공적으로 저장되었습니다.")
                else:
                    st.error("❌ 프롬프트 저장 중 오류가 발생했습니다.")
    else:
        st.error("⚠️ 이미지 대상을 입력하세요.")
