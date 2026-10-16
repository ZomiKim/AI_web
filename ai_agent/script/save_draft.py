"""메일 초안을 임시보관함에 저장하는 스크립트 (skill_email_write.md 용)

- config/email.env 의 계정 정보로 IMAP 접속해 초안을 임시보관함에 저장합니다.
- 저장만 하며 메일을 발송하지 않습니다. 발송은 사용자가 메일함에서 직접 합니다.
- 계정 정보(메일 주소, 비밀번호)는 화면에 출력하지 않습니다.

사용 예시 (ai_agent 폴더에서 실행):
    python script/save_draft.py folders
    python script/save_draft.py save --to partner@example.com --subject "[프로젝트명]검토 부탁드립니다" --body-file draft.txt
"""

import argparse
import base64
import imaplib
import re
import sys
import time
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / "config" / "email.env"

# 계정 이름: (메일 키, 비밀번호 키, 서버 키, 서버 기본값)
ACCOUNTS = {
    "naver": ("NAVER_EMAIL", "NAVER_PASSWORD", "NAVER_IMAP_SERVER", "imap.naver.com"),
    "google": ("GOOGLE_EMAIL", "GOOGLE_PASSWORD", "GOOGLE_IMAP_SERVER", "imap.gmail.com"),
}

# \Drafts 표시가 없는 서버를 위한 이름 후보 (IMAP 수정 UTF-7 표기 포함)
DRAFT_NAMES = ["Drafts", "임시보관함", "&x4TC3Lz0rQDVaA-", "[Gmail]/Drafts", "[Gmail]/&x4TC3Lz0rQDVaA-"]


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


def decode_utf7(name):
    """IMAP 수정 UTF-7 폴더 이름을 읽을 수 있는 문자열로 바꿉니다."""
    def repl(match):
        chunk = match.group(1)
        if not chunk:
            return "&"
        chunk = chunk.replace(",", "/")
        chunk += "=" * (-len(chunk) % 4)
        return base64.b64decode(chunk).decode("utf-16-be")
    return re.sub(r"&([^-]*)-", repl, name)


def list_folders(conn):
    """(플래그, 폴더 이름) 목록을 반환합니다."""
    status, data = conn.list()
    folders = []
    if status != "OK":
        return folders
    for raw in data:
        line = raw.decode(errors="replace")
        match = re.match(r'\((?P<flags>[^)]*)\) "?(?P<sep>[^"]*)"? (?P<name>.+)', line)
        if match:
            folders.append((match.group("flags"), match.group("name").strip('"')))
    return folders


def find_drafts(folders):
    """임시보관함 폴더 이름을 찾습니다. 못 찾으면 None."""
    for flags, name in folders:
        if "\\Drafts" in flags:
            return name
    names = {name for _, name in folders}
    for candidate in DRAFT_NAMES:
        if candidate in names:
            return candidate
    return None


def connect(account):
    env = load_env(ENV_PATH)
    user_key, pw_key, server_key, default_server = ACCOUNTS[account]
    user, password = env.get(user_key), env.get(pw_key)
    if not user or not password:
        print(f"[설정 없음] {user_key} 또는 {pw_key} 값이 비어 있습니다.")
        return None, None
    try:
        conn = imaplib.IMAP4_SSL(env.get(server_key) or default_server, 993)
        conn.login(user, password)
    except Exception as error:
        print(f"[접속 실패] {type(error).__name__}: {error}")
        return None, None
    return conn, user


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="메일 초안 임시보관함 저장")
    parser.add_argument("action", choices=["folders", "save"])
    parser.add_argument("--account", choices=list(ACCOUNTS), default="naver", help="기본값: naver")
    parser.add_argument("--to", help="받는 사람 메일 주소")
    parser.add_argument("--subject", help="메일 제목")
    parser.add_argument("--body-file", help="본문 텍스트 파일 경로 (UTF-8)")
    args = parser.parse_args()

    if args.action == "save" and not (args.to and args.subject and args.body_file):
        print("[입력 필요] save 에는 --to, --subject, --body-file 이 모두 필요합니다.")
        return

    conn, user = connect(args.account)
    if conn is None:
        return

    try:
        folders = list_folders(conn)
        drafts = find_drafts(folders)

        if args.action == "folders":
            for flags, name in folders:
                mark = "  <- 임시보관함" if name == drafts else ""
                print(f"- {decode_utf7(name)} ({flags}){mark}")
            if drafts is None:
                print("[확인 필요] 임시보관함 폴더를 찾지 못했습니다.")
            return

        if drafts is None:
            print("[확인 필요] 임시보관함 폴더를 찾지 못해 저장하지 않았습니다. folders 로 목록을 확인하세요.")
            return

        message = EmailMessage()
        message["From"] = user
        message["To"] = args.to
        message["Subject"] = args.subject
        message["Date"] = formatdate(localtime=True)
        message.set_content(Path(args.body_file).read_text(encoding="utf-8"))

        mailbox = f'"{drafts}"' if " " in drafts else drafts
        status, _ = conn.append(mailbox, "(\\Draft)", imaplib.Time2Internaldate(time.time()),
                                message.as_bytes())
        if status == "OK":
            print(f"[완료] 임시보관함({decode_utf7(drafts)})에 저장했습니다. 발송은 메일함에서 직접 해 주세요.")
        else:
            print(f"[실패] 저장 응답: {status}")
    finally:
        try:
            conn.logout()
        except Exception:
            pass


if __name__ == "__main__":
    main()
