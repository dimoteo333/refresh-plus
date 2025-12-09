# Refresh Plus 프로젝트 기획서

## 1. 프로젝트 개요
- 프로젝트 이름: Refresh Plus (신한은행 임직원 연성소 예약 플랫폼)
- 결과물 형태: 웹앱 + RAG 챗봇 + 자동화 배치 파이프라인
- 한 줄 요약: 공정한 티켓팅과 실시간 직접 예약을 통합하고 AI로 안내·알림을 제공하는 임직원 숙소 예약 플랫폼

## 2. 프로젝트 목적
- 업무 효율화: 기존 예약/확인/연락 프로세스를 자동화해 담당자·임직원 시간을 절약
- 문제 해결: 불공정·지연·알림 누락 문제를 해결하고 실시간 가용 정보를 투명하게 제공

## 3. 주요 기능 (3~6개)
- 공정 티켓팅 & 직접 예약: 포인트 기반 티켓팅 배치(매일 00:00 KST)와 lulu-lala 연동 즉시 예약(08:00~21:00) 병행
- 자동 크롤링 & 데이터 동기화: 숙소/FAQ/실시간 신청 현황을 Playwright 배치로 수집·DB 반영
- 실시간 알림 & PWA: 당첨/탈락, 찜한 숙소 가능 여부, 포인트 회복, 인기 숙소 변동을 푸시 알림으로 발송
- FAQ RAG 챗봇: Chainlit 위젯에서 FAQ 기반 검색·응답, 예약 정책/점수/취소 규정 안내
- 찜 & 추천: 최대 20개 찜, 내 점수 대비 가능 숙소 알림, 주말/휴일 필터 자동 적용
- 관리자/모니터링: Railway Cron 상태, 크롤링/티켓팅 로그, Sentry 모니터링(확장 시)

## 4. 사용 기술
- UI: Shadcn (Tailwind CSS) 기반 Next.js 15 (Vercel 배포)
- 백엔드: FastAPI (Python) + Railway 배포, 비즈니스 로직 서비스 계층 분리
- DB: Turso (SQLite Edge) 기본, 필요 시 PostgreSQL 확장
- 알림: PWA(iOS/Android/Web) + Firebase FCM 연동
- 챗봇: LangChain + Chainlit 위젯 + OpenAI 모델
- 크롤러: Playwright (RSA 로그인, FAQ/숙소/실시간 현황 크롤링)
- 인프라: Vercel(프론트), Railway(백엔드/크론), GitHub Actions CI/CD
- 기타: 로고 생성 nanobanana, 자료 조사·프롬프트 엔지니어링 perplexity, 코드 작성 Claude Code(메인) + Codex(서브/검수), 문서·단순 수정 cursor

## 5. 사용자 흐름 (User Flow)
1) 사용자가 웹앱 접속 및 로그인(JWT)
2) 숙소 리스트/필터 확인 → 상세 페이지 이동
3) 예약 선택
   - 티켓팅: 날짜 선택 → 신청 → PENDING 기록 → 자정 배치로 WON/LOST 결정 → 결과 알림
   - 직접 예약(08~21시): 연락처·동의 입력 → lulu-lala API POST → HTTP 302 성공 시 즉시 WON, 포인트 차감
4) 찜: 최대 20개 등록 → 점수 조건 충족 시 푸시 알림
5) FAQ/챗봇: Chainlit 위젯에 질문 → FAQ RAG 검색 → LLM 응답 제공
6) 알림: 당첨/탈락, 포인트 회복, 인기 숙소, 시간 임박 등 PWA 푸시 수신

## 6. AI 활용 내역
- 데이터 소스 준비: 기존 FAQ/숙소 데이터를 Playwright로 크롤링 후 RAG 인덱스 구축
- 프롬프트 엔지니어링: perplexity로 정책/FAQ 맥락 수집 후 LLM 응답 템플릿 최적화, Chainlit 대화 흐름 설계
- 코드 생성: Claude Code를 주 개발 도구로 사용하며 Codex는 검수/보조로 활용
- 챗봇/자동화: LangChain으로 FAQ 검색 체인 구성, OpenAI 모델로 응답 생성, Chainlit 위젯 임베드
- 알림: RAG/예약 이벤트 결과를 기반으로 FCM 푸시 트리거
- 캡처 TODO: 실제 배치 실행 화면, 프롬프트 입력/응답 스크린샷을 추후 삽입
