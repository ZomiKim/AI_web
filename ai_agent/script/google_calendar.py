"""구글 캘린더 연동 스크립트 (OAuth 인증 및 연동 확인)

- config/google_client.json 의 OAuth 클라이언트 정보로 인증합니다.
  (파일이 없으면 config/calendar.env 의 GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET 을 사용합니다.)
- 인증 토큰은 config/google_token.json 에 저장합니다. (Git 제외 대상)
- 클라이언트 정보와 토큰 값은 화면에 출력하지 않습니다.
- 일정 조회만 하며 일정을 등록·수정·삭제하지 않습니다.

사용 예시 (ai_agent 폴더에서 실행):
    python script/google_calendar.py auth     # 브라우저에서 구글 계정 로그인 후 토큰 저장
    python script/google_calendar.py check    # 캘린더 목록과 다가오는 일정 5개 조회
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
CLIENT_PATH = CONFIG_DIR / "google_client.json"
ENV_PATH = CONFIG_DIR / "calendar.env"
TOKEN_PATH = CONFIG_DIR / "google_token.json"

# 일정 등록 자동화를 위해 일정 읽기·쓰기 권한과 캘린더 목록 읽기 권한을 요청합니다.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
]


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


def make_flow():
    """OAuth 인증 흐름을 만듭니다. google_client.json 을 우선 사용합니다."""
    if CLIENT_PATH.exists():
        return InstalledAppFlow.from_client_secrets_file(str(CLIENT_PATH), SCOPES)

    env = load_env(ENV_PATH)
    if not env.get("GOOGLE_CLIENT_ID") or not env.get("GOOGLE_CLIENT_SECRET"):
        print("[실패] google_client.json 이 없고 calendar.env 에도 클라이언트 정보가 없습니다.")
        sys.exit(1)
    config = {
        "installed": {
            "client_id": env["GOOGLE_CLIENT_ID"],
            "client_secret": env["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [env.get("GOOGLE_REDIRECT_URI", "http://localhost")],
        }
    }
    return InstalledAppFlow.from_client_config(config, SCOPES)


def get_credentials(allow_login):
    """저장된 토큰을 읽고, 만료됐으면 갱신합니다. allow_login 이면 새로 로그인합니다."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif allow_login:
        creds = make_flow().run_local_server(port=0, open_browser=True)
    else:
        print("[확인 필요] 저장된 토큰이 없습니다. 먼저 auth 를 실행하세요.")
        sys.exit(1)

    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def check(creds):
    """캘린더 목록과 기본 캘린더의 다가오는 일정 5개를 출력합니다."""
    service = build("calendar", "v3", credentials=creds)

    calendars = service.calendarList().list().execute().get("items", [])
    print(f"[캘린더 목록] {len(calendars)}개")
    for cal in calendars:
        mark = " (기본)" if cal.get("primary") else ""
        print(f"- {cal.get('summary', '(이름 없음)')}{mark} / 권한: {cal.get('accessRole')}")

    now = datetime.now(timezone.utc).isoformat()
    events = service.events().list(calendarId="primary", timeMin=now, maxResults=5,
                                   singleEvents=True, orderBy="startTime").execute().get("items", [])
    print(f"\n[다가오는 일정] {len(events)}건")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        print(f"- {start} | {event.get('summary', '(제목 없음)')}")

    print("\n[완료] 구글 캘린더 연동이 확인되었습니다.")


def main():
    parser = argparse.ArgumentParser(description="구글 캘린더 연동 및 확인")
    parser.add_argument("command", choices=["auth", "check"])
    args = parser.parse_args()

    if args.command == "auth":
        get_credentials(allow_login=True)
        print("[완료] 인증 토큰을 config/google_token.json 에 저장했습니다.")
    check(get_credentials(allow_login=False))


if __name__ == "__main__":
    main()
