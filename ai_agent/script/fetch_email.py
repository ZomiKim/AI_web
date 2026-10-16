"""
메일 수집 스크립트 (skill_email.md 요약용)

- config/email.env 의 계정 정보로 네이버·구글 메일함(INBOX)에 IMAP 접속합니다.
- 메일함을 읽기 전용으로 열어, 실행해도 '읽음' 상태가 바뀌지 않습니다.
- 계정 정보(메일 주소, 비밀번호)는 화면에 출력하지 않습니다.
- 결과는 화면에만 출력합니다. 출력 내용을 복사해 비서에게 전달하세요.

사용 예시 (ai_agent 폴더에서 실행):
    python script/fetch_email.py --since 2026-08-03 --include-read
"""

import argparse
import email
import imaplib
import re
import sys
from datetime import datetime
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / "config" / "email.env"

# (표시 이름, 메일 키, 비밀번호 키, 서버 키, 서버 기본값)
ACCOUNTS = [
    ("네이버", "NAVER_EMAIL", "NAVER_PASSWORD", "NAVER_IMAP_SERVER", "imap.naver.com"),
    ("구글", "GOOGLE_EMAIL", "GOOGLE_PASSWORD", "GOOGLE_IMAP_SERVER", "imap.gmail.com"),
]

BODY_LIMIT = 1500  # 메일 1건당 출력할 본문 최대 글자 수


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


def decode_text(value):
    """메일 헤더(제목, 보낸이)의 인코딩을 풀어 문자열로 반환합니다."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def html_to_text(html):
    """HTML 본문에서 태그를 제거해 텍스트만 남깁니다."""
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    return unescape(text)


def extract_body(message):
    """본문을 추출합니다. text/plain 우선, 없으면 text/html을 텍스트로 변환합니다."""
    plain, html = None, None
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition", "").lower().startswith("attachment"):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except LookupError:
            text = payload.decode("utf-8", errors="replace")
        if part.get_content_type() == "text/plain" and plain is None:
            plain = text
        elif part.get_content_type() == "text/html" and html is None:
            html = text
    body = plain if plain else html_to_text(html or "")
    body = re.sub(r"\s+", " ", body).strip()
    if len(body) > BODY_LIMIT:
        body = body[:BODY_LIMIT] + " ...(이하 생략)"
    return body


def fetch_account(label, user, password, server, since, include_read):
    """한 계정의 INBOX에서 조건에 맞는 메일을 가져와 출력합니다."""
    print(f"\n========== ({label}) ==========")
    try:
        conn = imaplib.IMAP4_SSL(server, 993)
        conn.login(user, password)
    except Exception as error:
        print(f"[접속 실패] {type(error).__name__}: {error}")
        return

    try:
        conn.select("INBOX", readonly=True)
        criteria = ["SINCE", since.strftime("%d-%b-%Y")]
        if not include_read:
            criteria.append("UNSEEN")
        status, data = conn.uid("search", None, *criteria)
        uids = data[0].split() if status == "OK" and data[0] else []

        if not uids:
            print("받은 메일 없음")
            return

        print(f"총 {len(uids)}건")
        for index, uid in enumerate(uids, start=1):
            status, msg_data = conn.uid("fetch", uid, "(FLAGS BODY.PEEK[])")
            if status != "OK" or not msg_data or msg_data[0] is None:
                print(f"\n--- [{index}] 가져오기 실패 (UID {uid.decode()}) ---")
                continue
            flags = msg_data[0][0].decode(errors="replace")
            message = email.message_from_bytes(msg_data[0][1])
            try:
                received = parsedate_to_datetime(message.get("Date")).strftime("%Y-%m-%d %H:%M")
            except Exception:
                received = "[날짜 확인 불가]"
            read_state = "읽음" if "\\Seen" in flags else "안읽음"

            print(f"\n--- [{index}] ---")
            print(f"수신일시: {received} ({read_state})")
            print(f"보낸이: {decode_text(message.get('From'))}")
            print(f"제목: {decode_text(message.get('Subject'))}")
            print(f"본문: {extract_body(message)}")
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="메일 수집 (skill_email.md 요약용)")
    parser.add_argument("--since", required=True, help="조회 시작일 (예: 2026-08-03)")
    parser.add_argument("--include-read", action="store_true", help="읽은 메일도 포함")
    args = parser.parse_args()

    since = datetime.strptime(args.since, "%Y-%m-%d")
    env = load_env(ENV_PATH)

    print(f"수집 구간: {since:%Y-%m-%d} 00:00 ~ {datetime.now():%Y-%m-%d %H:%M}")
    print(f"읽은 메일 포함: {'예' if args.include_read else '아니오 (안읽음만)'}")

    if not env:
        print(f"[설정 없음] {ENV_PATH} 파일을 찾을 수 없거나 비어 있습니다.")
        return

    for label, user_key, pw_key, server_key, default_server in ACCOUNTS:
        user, password = env.get(user_key), env.get(pw_key)
        if not user or not password:
            print(f"\n========== ({label}) ==========")
            print(f"[설정 없음] {user_key} 또는 {pw_key} 값이 비어 있어 건너뜁니다.")
            continue
        server = env.get(server_key) or default_server
        fetch_account(label, user, password, server, since, args.include_read)


if __name__ == "__main__":
    main()
