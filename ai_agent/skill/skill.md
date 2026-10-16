---
name: 메일요약
description: 이메일 환경설정과 이메일 요약 업무 지침을 확인하여 새 메일을 조회하고 요약 보고하는 업무
disable-model-invocation: true
---

# 이메일 요약 업무

사용자가 `메일요약` 명령을 실행하면 다음 순서로 작업한다.

## 1. 환경설정 확인

먼저 다음 파일을 확인한다.

- `${CLAUDE_PROJECT_DIR}/ai_agent/config/email.env`

환경변수의 실제 값이나 비밀번호, 토큰은 사용자에게 출력하지 않는다.

필요한 환경변수가 존재하는지만 확인한다.

## 2. 업무 지침 확인

다음 파일을 읽고 해당 규칙을 따른다.

- `${CLAUDE_PROJECT_DIR}/ai_agent/workspace/01_Daily/skill/skill_email.md`
- `${CLAUDE_PROJECT_DIR}/ai_agent/workspace/01_Daily/skill/skill_email_write.md`

## 3. 메일 조회

설정된 이메일 연결 방식에 따라 메일을 조회한다.

- 조회 시작 시점: `ai_agent` 폴더에서 `python script/notion_api.py last`로 확인한 노션 최신 브리핑의 '날짜'
- 조회 명령: `python script/fetch_email.py --since "YYYY-MM-DD HH:MM" --include-read` (읽은 메일 포함)

## 4. 요약

skill_email.md에 정의된 형식과 규칙에 따라 메일을 요약한다.

## 5. 노션 업로드

- 요약본을 `workspace/01_Daily/YYYY-MM-DD_HHMM_이메일브리핑.md`로 저장한다.
- `python script/notion_api.py brief "[추가요청] 이메일 브리핑 요약 / N건 (YYYY-MM-DD HH:mm)" <요약본 경로>`로 업로드한다.
- `[검증 완료]`를 확인한 뒤 skill_email.md 8번 절차에 따라 원본 메일 임시 파일을 삭제한다.

## 6. 보고

최종 결과만 사용자에게 한국어로 보고한다.

API 또는 이메일 데이터에 존재하지 않는 내용은 추측하지 않는다.
