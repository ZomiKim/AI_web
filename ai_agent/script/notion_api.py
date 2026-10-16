"""노션 데이터베이스 연동 스크립트 (skill_email.md 7번 적재용)

- config/email.env 의 NOTION_TOKEN, NOTION_DATABASE_ID 값으로 노션 API를 호출합니다.
- 토큰은 화면에 출력하지 않습니다.
- 데이터베이스는 노션에서 연동 앱(Connections)에 공유되어 있어야 합니다.

사용 예시 (ai_agent 폴더에서 실행):
    python script/notion_api.py schema
    python script/notion_api.py last
    python script/notion_api.py upload payload.json
    python script/notion_api.py brief "[정기] 이메일 브리핑 요약 / 3건 (2026-08-03 09:00)" workspace/01_Daily/2026-08-03_0900_이메일브리핑.md
    python script/notion_api.py verify <페이지 ID> workspace/01_Daily/2026-08-03_0900_이메일브리핑.md

brief는 업로드 직후 verify를 자동으로 실행합니다.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / "config" / "email.env"
NOTION_VERSION = "2022-06-28"
RICH_TEXT_LIMIT = 2000


def load_env(path):
    """KEY="VALUE" 형식의 env 파일을 읽어 dict로 반환합니다."""
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def call(method, url, token, body=None):
    """노션 API를 호출하고 (상태 코드, 응답 dict)를 반환합니다."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def print_error(status, res):
    print(f"[실패] {status} {res.get('code')}: {res.get('message')}")


def show_schema(token, db_id):
    """데이터베이스의 컬럼 이름과 형식을 출력합니다."""
    status, res = call("GET", f"https://api.notion.com/v1/databases/{db_id}", token)
    if status != 200:
        print_error(status, res)
        return
    title = "".join(t.get("plain_text", "") for t in res.get("title", []))
    print(f"데이터베이스: {title}")
    for name, prop in res.get("properties", {}).items():
        print(f"- {name} ({prop['type']})")


def upload(token, db_id, payload_path):
    """payload JSON(properties 등)을 데이터베이스에 새 행으로 추가합니다."""
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    payload["parent"] = {"database_id": db_id}
    status, res = call("POST", "https://api.notion.com/v1/pages", token, payload)
    if status != 200:
        print_error(status, res)
        return
    print(f"[완료] {res.get('url')}")


def show_last(token, db_id):
    """'날짜'가 가장 최근인 브리핑의 제목과 날짜를 출력합니다."""
    body = {"sorts": [{"property": "날짜", "direction": "descending"}], "page_size": 1}
    status, res = call("POST", f"https://api.notion.com/v1/databases/{db_id}/query", token, body)
    if status != 200:
        print_error(status, res)
        return
    results = res.get("results", [])
    if not results:
        print("[기록 없음] 데이터베이스에 브리핑이 없습니다.")
        return
    props = results[0]["properties"]
    title = "".join(t.get("plain_text", "") for t in props["제목"]["title"])
    date = (props["날짜"].get("date") or {}).get("start")
    print(f"최근 브리핑: {title}")
    print(f"날짜: {date}")


def upload_brief(token, db_id, title, text_path):
    """브리핑 텍스트 파일을 '제목 / 날짜 / 메일내용요약' 컬럼으로 업로드합니다.

    rich_text는 조각당 2000자 제한이 있어 2000자 단위로 나눠 담습니다.
    """
    text = Path(text_path).read_text(encoding="utf-8").strip()
    chunks = [text[i:i + RICH_TEXT_LIMIT] for i in range(0, len(text), RICH_TEXT_LIMIT)]
    payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "제목": {"title": [{"text": {"content": title}}]},
            "날짜": {"date": {"start": datetime.now().astimezone().isoformat(timespec="seconds")}},
            "메일내용요약": {"rich_text": [{"text": {"content": chunk}} for chunk in chunks]},
        },
    }
    status, res = call("POST", "https://api.notion.com/v1/pages", token, payload)
    if status != 200:
        print_error(status, res)
        return
    print(f"[완료] {len(text)}자 / {len(chunks)}조각 / {res.get('url')}")
    verify(token, res["id"], text_path)


def verify(token, page_id, text_path):
    """업로드된 페이지의 '메일내용요약'이 브리핑 파일과 같은지 확인합니다."""
    status, res = call("GET", f"https://api.notion.com/v1/pages/{page_id}", token)
    if status != 200:
        print_error(status, res)
        return False
    if res.get("archived") or res.get("in_trash"):
        print("[검증 실패] 페이지가 보관(휴지통) 상태입니다.")
        return False
    rich_text = res["properties"]["메일내용요약"]["rich_text"]
    uploaded = "".join(t.get("plain_text", "") for t in rich_text)
    original = Path(text_path).read_text(encoding="utf-8").strip()
    if uploaded != original:
        print(f"[검증 실패] 본문 불일치 (업로드 {len(uploaded)}자 / 원본 {len(original)}자)")
        return False
    print(f"[검증 완료] 본문 {len(uploaded)}자가 원본과 일치합니다.")
    return True


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] not in ("schema", "last", "upload", "brief", "verify"):
        print("사용법: python script/notion_api.py schema | last | upload <payload.json>"
              " | brief <제목> <브리핑.md> | verify <페이지 ID> <브리핑.md>")
        return

    env = load_env(ENV_PATH)
    token, db_id = env.get("NOTION_TOKEN"), env.get("NOTION_DATABASE_ID")
    if not token or not db_id:
        print(f"[설정 없음] {ENV_PATH} 에 NOTION_TOKEN 또는 NOTION_DATABASE_ID 값이 없습니다.")
        return

    if sys.argv[1] == "schema":
        show_schema(token, db_id)
    elif sys.argv[1] == "last":
        show_last(token, db_id)
    elif sys.argv[1] == "brief":
        if len(sys.argv) < 4:
            print("[입력 필요] brief 뒤에 제목과 브리핑 파일 경로를 지정하세요.")
        else:
            upload_brief(token, db_id, sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "verify":
        if len(sys.argv) < 4:
            print("[입력 필요] verify 뒤에 페이지 ID와 브리핑 파일 경로를 지정하세요.")
        else:
            verify(token, sys.argv[2], sys.argv[3])
    elif len(sys.argv) < 3:
        print("[입력 필요] upload 뒤에 payload JSON 파일 경로를 지정하세요.")
    else:
        upload(token, db_id, sys.argv[2])


if __name__ == "__main__":
    main()
