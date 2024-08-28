import streamlit as st
import requests
import toml
import pathlib

# 페이지 설정 - 아이콘과 제목 설정
st.set_page_config(
    page_title="교사용 교육 도구 홈",  # 브라우저 탭에 표시될 제목
    page_icon="🧑‍🏫",  # 브라우저 탭에 표시될 아이콘 (이모지 또는 이미지 파일 경로)
)


# Streamlit의 기본 메뉴와 푸터 숨기기
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden; }
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# secrets.toml 파일 경로
secrets_path = pathlib.Path(__file__).parent.parent / ".streamlit/secrets.toml"

# secrets.toml 파일 읽기
with open(secrets_path, "r") as f:
    secrets = toml.load(f)

# Notion API 설정
NOTION_API_KEY = secrets["notion"]["api_key"]
NOTION_DATABASE_ID = secrets["notion"]["database_id"]
NOTION_API_QUERY_URL = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
NOTION_PAGE_URL = f"https://api.notion.com/v1/pages"

# 비밀번호를 사용하여 프롬프트 검색
def search_prompt_by_password(page_type, password):
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
                        "equals": page_type
                    }
                },
                {
                    "property": "password",
                    "rich_text": {
                        "equals": password
                    }
                }
            ]
        }
    }
    response = requests.post(NOTION_API_QUERY_URL, headers=headers, json=data)
    if response.status_code == 200:
        results = response.json().get("results", [])
        return results
    else:
        st.error(f"⚠️ Notion API 호출 실패: {response.status_code} - {response.text}")
        return []

# 활동 코드를 사용하여 프롬프트 삭제
def delete_prompt_by_activity_code(activity_code):
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "filter": {
            "property": "setting_name",
            "rich_text": {
                "equals": activity_code
            }
        }
    }
    response = requests.post(NOTION_API_QUERY_URL, headers=headers, json=data)
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            for result in results:
                page_id = result["id"]
                try:
                    # 페이지를 삭제하는 대신 보관처리(archive)로 변경
                    archive_data = {"archived": True}
                    delete_response = requests.patch(f"{NOTION_PAGE_URL}/{page_id}", headers=headers, json=archive_data)
                    if delete_response.status_code == 200:
                        st.success(f"🎉 활동 코드 '{activity_code}'에 해당하는 프롬프트가 성공적으로 삭제 처리되었습니다.")
                    else:
                        st.error(f"❌ 활동 코드 '{activity_code}'에 해당하는 프롬프트 삭제 중 오류가 발생했습니다. 상태 코드: {delete_response.status_code} - {delete_response.text}")
                except Exception as e:
                    st.error(f"❌ 활동 코드 '{activity_code}'에 해당하는 프롬프트 삭제 중 예외가 발생했습니다: {str(e)}")
        else:
            st.warning("⚠️ 해당 활동 코드에 대한 프롬프트를 찾을 수 없습니다.")
    else:
        st.error(f"⚠️ Notion API 호출 실패: {response.status_code} - {response.text}")

# 교사용 인터페이스
st.title("🛠️ 교사용 프롬프트 관리 도구")

st.markdown("""
이 도구를 사용하여 저장된 프롬프트를 검색하고 삭제할 수 있습니다.
""")

# 1. 이미지 분석, 텍스트 생성, 이미지 생성 중 선택
page_type = st.selectbox("분석/생성 유형을 선택하세요:", ["vision", "text", "image"])

# 2. 비밀번호 입력 및 프롬프트 검색
password = st.text_input("🔒 비밀번호를 입력하세요:", type="password").strip()

if st.button("🔍 프롬프트 검색"):
    if password:
        results = search_prompt_by_password(page_type, password)
        if results:
            st.write("**검색된 프롬프트:**")
            for result in results:
                st.write(f"**활동 코드:** {result['properties']['setting_name']['rich_text'][0]['text']['content']}")
                st.write(f"**프롬프트:** {result['properties']['prompt']['rich_text'][0]['text']['content']}")
                st.write("---")
        else:
            st.warning("⚠️ 해당 비밀번호에 대한 프롬프트를 찾을 수 없습니다.")
    else:
        st.error("⚠️ 비밀번호를 입력하세요.")

# 3. 활동 코드를 입력하여 프롬프트 삭제
activity_code = st.text_input("🗑️ 삭제할 활동 코드를 입력하세요:").strip()

if st.button("🗑️ 프롬프트 삭제"):
    if activity_code:
        delete_prompt_by_activity_code(activity_code)
    else:
        st.error("⚠️ 삭제할 활동 코드를 입력하세요.")
