<h1>
    <img src="images/icon-512x512.png" width="50" style="vertical-align: middle;" />
    Refresh+
</h1>

<img src="images/image.png" width="70%" />

## 1. 프로젝트 개요

- 프로젝트 이름: **Refresh+** (신한은행 임직원 연성소 예약 앱)
- 결과물 형태: **하이브리드 웹앱** (+ RAG 챗봇, 자동화 배치 파이프라인, AI 생성물)
- 한 줄 요약:

<aside>
🛌

AI로 더 똑똑해진, 당신만을 위한 맞춤형 연성소 예약 플랫폼 - Refresh+

</aside>

---

## 2. 프로젝트 목적

**주요 목적: 문제 해결 + 업무 효율화 + AI 창작 실험**

### 기존 시스템의 한계

![image.png](images/image%201.png)

<aside>
😰

**UX 문제**

직관적이지 못한 검색과 레거시한 화면

</aside>

<aside>
📉

**정보 부족**

숙소 평가 지표, 예약 알림, 가성비 정보 부재

</aside>

<aside>
🤷

**개인화 부족**

사용자 맞춤 추천 기능 없음

</aside>

<aside>
💰

**운영 비용**

지속적인 외주업체 유지보수 비용 발생

</aside>

---

## Refresh+의 해결책

![image.png](images/image%202.png)

![image.png](images/image%203.png)

### **AI 기반 통합 웹/앱 End-to-End 자체 구축 및 배포**

본 프로젝트는 단순한 기능 개선을 넘어 **AI를 활용한 빠른 개발/배포 실현**이라는 의미 있는 결과를 도출했습니다. 은행이 관리하고 있는 외주개발 사이트에 대해 **내부 인력이 AI의 지원을 받아 짧은 기간 내에 자체 구축**함으로써 다음과 같은 효과를 달성했습니다:

- **개발 생산성 향상:** AI 코딩 보조 도구를 활용해 **전통적 개발 기간 단축**
- **기술 역량 강화:** 내부 개발 인력의 AI 도구 활용 경험 축적 및 역량 개발
- **자체 커스터마이징 가능:** 향후 기능 개선 및 유지보수를 자체적으로 진행 가능한 기반 구축

이를 통해 임직원은 **더 빠르고, 더 똑똑하게, 더 만족도 높은 숙소를 예약**할 수 있는 경험을 얻게 되며, 

조직 차원에서는 **숙소 예약 시스템의 현대화, 사용자 만족도 증대, 그리고 AI 기반 개발 방식의 성공적 사례 창출**이라는 복합적 효과를 기대할 수 있습니다.

## 3. 주요 기능

**Refresh+**는 **AI 기반 데이터 분석**과 **사용자 맞춤형 추천**을 통해 임직원의 연성소 예약 경험을 혁신합니다.

---

### 기능 1. 요일별 숙소 예상 점수 제공

<aside>
📊

과거 데이터 기반으로 **요일별 예측 당첨 점수**를 제공하여 예약 성공률을 높입니다.

</aside>

**핵심 가치**

- 과거 요일별 연성소의 점수 정보를 기반으로 예측 당첨 점수 산출
- 데이터 기반 의사결정으로 사용자의 예약 경험 향상
- 언제 신청해야 당첨 확률이 높은지 한눈에 파악

**작동 방식**

- 실시간 신청 점수 데이터 자동 수집
- 요일별 패턴 분석을 통한 AI 예측 알고리즘 적용
- 사용자에게 최적의 예약 타이밍 제안

<img src="images/image 4.png" width="70%" />
<img src="images/image 5.png" width="70%" />

---

### 기능 2. SOL 점수 (숙박 효율 점수) 시스템

<aside>
🏆

**가격과 점수를 종합한 가성비 지표**로 최적의 숙소를 빠르게 찾을 수 있습니다.

</aside>

**핵심 가치**

- 네이버 호텔 최저가와 예상 점수를 알고리즘으로 결합
- 가성비를 객관적 수치로 표현하여 의사결정 지원
- 사용자가 최적의 숙소를 빠르게 식별 가능

**계산 방식**

- 숙소 최저가 데이터 자동 수집
- 예상 신청 점수와의 균형 분석
- SOL 점수 알고리즘으로 가성비 수치화

```bash
 📐 계산 로직
  1단계: 효율성 계산
  효율성 = 온라인 최저가 ÷ (신청 점수 × 가중치)

  예시:
  - 숙소 A: 온라인 최저가 200,000원, 신청 점수 50점 (가중치 1.3)
    - 효율성 = 200,000 ÷ (50 × 1.3) = 3,076.92
  - 숙소 B: 온라인 최저가 150,000원, 신청 점수 95점 (가중치 0.7)
    - 효율성 = 150,000 ÷ (95 × 0.7) = 2,256.53

  2단계: 가중치 시스템
  신청 점수에 따라 차등 가중치를 적용하여 높은 점수를 요구하는 숙소의 효율성을 보정합니다.

  | 신청 점수  | 가중치  | 의미                                    |
  |----------|------|-----------------------------------------|
  | 90점 이상 | 0.7배 | 높은 점수 요구 → 가중치 낮춤 (SOL 점수 상승 효과) |
  | 70~89점  | 1.0배 | 중간 범위 → 가중치 유지                      |
  | 70점 미만 | 1.3배 | 낮은 점수 요구 → 가중치 높임 (SOL 점수 하락 효과) |

  가중치 적용 이유:
  - 90점 이상 고득점이 필요한 숙소는 진입장벽이 높지만, 온라인 최저가가 비싸면 효율적
  - 70점 미만 저득점으로 예약 가능한 숙소는 많지만, 온라인 최저가가 저렴하면 효율성이 낮음

  3단계: Min-Max 정규화

  모든 숙소의 효율성 값을 0~100점 척도로 변환합니다.

  SOL 점수 = ((효율성 - 최소 효율성) ÷ (최대 효율성 - 최소 효율성)) × 100

  결과:
  - SOL 점수 100점 = 전체 숙소 중 가성비 최고
  - SOL 점수 0점 = 전체 숙소 중 가성비 최저
```

> "같은 점수라면 더 좋은 숙소를, 같은 숙소라면 더 낮은 점수로 예약하세요!"
> 

---

### 기능 3. 사용자 맞춤형 숙소 추천 및 즐겨찾기

<aside>
✨

**내 점수에 딱 맞는 숙소**를 자동으로 추천하고, 관심 숙소의 예약 알림을 받을 수 있습니다.

</aside>

**핵심 가치**

- 현재 보유 점수 기반 예약 가능한 숙소 자동 필터링
- 가고 싶은 연성소 즐겨찾기 등록
- 맞춤형 알림 수신으로 예약 기회 놓치지 않음

**맞춤형 추천 프로세스**

1. 사용자의 현재 점수 확인
2. 예약 가능성이 높은 숙소 자동 필터링
3. SOL 점수 기반 최적 숙소 우선 추천

**즐겨찾기 기능**

- 관심 숙소를 즐겨찾기에 추가
- 해당 숙소 예약 오픈 시 자동 알림

<img src="images/eb63cc21-2bb6-4dcd-adbb-0de6928a4d51.png" width="70%" />
<img src="images/image%206.png" width="70%" />

---

### 기능 4. 24시간 AI 상담 챗봇

<aside>
🤖

**언제든지 궁금한 점을 물어보세요.** AI 챗봇이 24시간 실시간으로 답변해드립니다.

</aside>

**핵심 가치**

- LangChain 및 OpenAI 기반 지능형 대화 엔진
- 예약, 취소 및 규정 관련 질문에 실시간 응답
- 연성소 FAQ 기반 정확한 가이드 제공

**기술 구성**

- **RAG (검색 증강 생성)**: 연성소 FAQ 문서를 기반으로 정확한 답변
- **자연어 처리**: 사용자 질문을 이해하고 맥락에 맞는 응답

**주요 상담 영역**

- 예약 방법 및 절차 안내
- 취소/변경 규정 설명

<img src="images/image%207.png" width="70%" />

---

### 기능 5. 숙소 상세정보 AI 요약 서비스

<aside>
⚡

**긴 설명은 이제 그만!** AI가 숙소 핵심 정보를 3줄로 요약해드립니다.

</aside>

**핵심 가치**

- 장문의 숙소 설명을 3줄 핵심 요약으로 자동 변환
- 정보 소비 시간 대폭 단축
- 핵심만 빠르게 파악하고 빠른 의사결정

**AI 요약 프로세스**

1. 숙소 상세 설명 자동 수집
2. OpenAI GPT 모델로 핵심 정보 추출
3. 3줄 요약 형태로 사용자에게 제공

**요약 포함 내용**

- 숙소의 주요 특징과 장점
- 위치 및 접근성 정보
- 주변 편의시설 및 추천 포인트


<img src="images/c0ae840f-8b28-4b5a-ab83-1acb67c1f28d.png" width="70%" />
<img src="images/image%208.png" width="70%" />

## 4. 사용 기술

| **분야** | **기술 스택** |
| --- | --- |
| **프론트엔드** | Next.js 15, Shadcn (Tailwind CSS 기반), TypeScript, Vercel 배포 |
| **백엔드** | FastAPI (Python), Railway 배포, 비즈니스 로직 서비스 계층 분리 |
| **데이터베이스** | Turso (SQLite) |
| **알림 시스템** | PWA (iOS/Android/Web 통합 지원) |
| **AI 챗봇** | LangChain + Chainlit + OpenAI 모델 |
| **웹 크롤러** | Playwright (SSO 로그인 지원, 숙소/FAQ/실시간 현황 크롤링) |
| **인프라** | Vercel (프론트엔드), Railway (백엔드/크론 작업) |
| **AI 생성 도구** | Claude (코드 작성 메인), Codex (검수/서브), Cursor (문서 및 단순 수정), Perplexity (자료 조사·프롬프트 엔지니어링), 나노바나나 (로고 생성), ChatGPT (자료 조사 및 검토) |
| **LLM 모델** | OpenAI GPT 시리즈 (챗봇 및 요약 기능) |

## 5. 사용자 흐름(User Flow)

![Mermaid Chart - Create complex, visual diagrams with text.-2025-12-10-134844.png](images/Mermaid_Chart_-_Create_complex_visual_diagrams_with_text.-2025-12-10-134844.png)

<aside>
🔄

**데이터 자동 수집** → **실시간 검색** → **AI 분석** → **즉시 추천** → **예약 알림**까지 전 과정을 자동으로 처리하는 AI 기반 통합 숙소 추천 플랫폼

</aside>

---

### 0단계. 숙소 데이터 자동 수집 (매일 상시 갱신)

<aside>
📊

서비스의 모든 추천은 **자동 수집된 실시간 데이터**를 기반으로 합니다.

</aside>

**자동 수집 프로세스**

- 매일 **08시~21시** 사이 **20분 간격** 반복 배치를 통해 숙소 정보 자동 수집

**수집 항목**

- 숙소 상세 정보
- 날짜별 실시간 신청 점수
- 숙소 최저가

**기술 스택**

- **수집 방식**: Playwright 기반 파이썬 크롤링
- **데이터 출처**: 네이버 호텔 + 신한은행 연성소 사이트

> **사람이 직접 갱신하지 않아도, 모든 숙소 정보는 자동으로 최신화됩니다.**
> 

---

### 1단계. 사용자가 숙소 검색

<aside>
👤

사용자는 Refresh+ 검색 화면에서 **원하는 날짜와 숙소를 검색**합니다.

</aside>

**검색 예시**

> "2026년 1월 10일(토) / 포시즌스 호텔"
> 

**프론트엔드 환경**

- **배포 플랫폼**: Vercel (AWS, 싱가포르 리전)

---

### 2단계. 검색 요청이 백엔드로 전달

<aside>
🚀

사용자의 검색 요청은 **즉시 서버로 전달됩니다.**

</aside>

**백엔드 환경**

- **배포 플랫폼**: Railway (AWS, 싱가포르 리전)
- **프레임워크**: FastAPI

---

### 3단계. 실시간 데이터 조회

<aside>
🔎

백엔드는 DB에서 **해당 날짜의 실제 예약 데이터**를 조회합니다.

</aside>

**조회 항목**

- 해당 날짜의 네이버 호텔 **최저가**
- **실시간 신청 점수**
- **현재 신청 인원**

**데이터베이스**

- Turso (SQLite, 일본 리전)

> 단순 검색이 아니라 **"실제 예약 가능성과 경쟁률"까지 동시에 분석**합니다.
> 

---

### 4단계. AI 분석 및 점수 생성

<aside>
🤖

조회된 데이터를 기반으로 **AI 기반 자동 분석을 수행합니다.**

</aside>

**AI 분석 내용**

- 해당 날짜·요일 기반 **예측 신청 점수 계산**
- 숙소의 **SOL 점수(가격 대비 효율 점수)** 산출
- OpenAI 기반 AI가 **숙소 핵심 정보 3줄 요약 자동 생성**

> 사용자는 **가격·경쟁률·추천 이유를 한 번에 확인**할 수 있습니다.
> 

---

### 5단계. 분석 결과 프론트엔드로 전달

<aside>
↩️

데이터 조회 + AI 분석이 모두 완료된 결과가 **다시 사용자 화면으로 전달됩니다.**

</aside>

---

### 6단계. 사용자 화면에 실시간 추천 표시

<aside>
✅

사용자는 실제 화면에서 다음 정보를 **즉시 확인**합니다.

</aside>

**화면 표시 정보**

- 2026년 1월 10일(토) 포시즌스 **상세 정보**
- **실시간 신청 점수**
- **AI 3줄 요약**
- **예측 점수 기반 추천 여부**

> **"언제, 어디가, 왜 좋은지"를 한 번에 이해할 수 있는 구조입니다.**
> 

---

### 7단계. 예약 알림 자동 발송

<aside>
⏰

사용자가 원하는 날짜에 **알림을 설정하면**, 해당 숙소 예약이 오픈되는 날짜에 맞춰 **푸시 알림이 자동 발송**됩니다.

</aside>

---

### 🏗️ 서비스 구성 특징

<aside>
🔧

**Vercel + Railway + Turso 분리**
프론트엔드와 백엔드, DB 모두를 독립적으로 관리하여 최적으로 운영

</aside>

<aside>
☁️

**클라우드 기반**
어디서든 안정적으로 접근 가능하고, 유지 보수가 쉬움

</aside>

<aside>
🤖

**AI 맞춤형 서비스**
OpenAI를 통해 사용자 맞춤형 기능들(추천, 요약, 챗봇) 제공

</aside>

<aside>
⚙️

**자동화**
Playwright 크롤러로 매일 숙소 정보 및 숙소 가격 갱신

</aside>

![image.png](images/image%209.png)

![image.png](images/image%2010.png)

## 6. AI 활용 내역

본 프로젝트는 AI를 단순한 보조 도구가 아닌 **핵심 개발 엔진**으로 활용하여 짧은 기간에 실제로 동작하는 복잡한 기능들을 구현했습니다. 다음은 각 단계별 AI 활용 상황입니다.

## 1. LLM 어시스턴트를 통한 연구 및 전략 수립

### Perplexity - 자료조사, 프롬프트 엔지니어링, 연구 담당

- 프로젝트 초반 숙소 예약 시스템의 시스템 구조 및 기반 코드 제공

![image.png](images/ed5b7343-22a0-4772-ba92-f62a7c90b3b0.png)

![image.png](images/image%2011.png)

<aside>
🚊

- 필요한 기능들에 대해 **각 단계별로 구현**할 수 있도록 **기능에 대한 설명 제공**
- 사용하고자 하는 기술 스택은 **미리 머리속에 구상 후 프로젝트 전반 설계** 요청
</aside>

- 공식 문서들을 참조한 **프롬프트 엔지니어링** 전략 수립

![image.png](images/image%2012.png)

```bash
# Identity (역할)
You are a Python backend engineer specializing in data pipeline and batch processing systems.

# Instructions (지침)
Modify the `today_accommodation_realtime.py` crawler to implement the following logic:

## Data Loading Rules
- Load only accommodation data that opened on the current batch execution date
- Insert data into `today_accommodation_info` SQLite database

## Data Cleanup Logic  
- Before inserting new data, check all existing rows in the database
- Compare the date portion of `updated_at` column with current batch execution date
- Delete all rows where `updated_at` date does not match today's date
- This ensures the table contains only fresh data loaded on the current day

## Batch Schedule
- This batch runs repeatedly between 08:00 and 21:00 daily
- Each execution should perform cleanup first, then load new data

# Context (컨텍스트)
<current_code>
# Paste your existing today_accommodation_realtime.py code here if needed
</current_code>

<database_schema>
Table: today_accommodation_info
- Relevant columns include updated_at (datetime/timestamp)
- Database type: SQLite
</database_schema>

```

- 그 외 다양한 아이디어 검증, 연구 조사 및 알고리즘 확인 진행

<aside>
🛖

해당 Refresh+를 위한 Perplexity ‘공간’을 만들어, 본 프로젝트의 내용을 연속성있게 질문하고 검증할 수 있었음

![image.png](images/image%2013.png)

</aside>

### ChatGPT - 빠른 확인 및 문제해결

**역할**

- 개발 중 발생하는 오류 로그 분석 및 빠른 해결
- 배포 과정에서 발생한 오류 로그에 대한 분석 진행

![image.png](images/image%2014.png)

![image.png](images/image%2015.png)

- 시연 영상을 위한 스크립트 및 스토리보드 작성

![image.png](images/image%2016.png)

![image.png](images/image%2017.png)

---

## 2. AI 코딩 에이전트를 통한 개발 구현

<aside>
💼

- UI/UX 관점에서 사용자 동선과 화면 목적을 먼저 정의한 뒤 구현을 요청
- 프론트 구현 시 연동할 백엔드 API와 데이터 구조를 함께 명시
- 기존 로직은 재사용하고 실제 서비스의 동작에 대해 자동화된 테스트 진행 요청
</aside>

![개발화면.png](images/a971a344-e6f8-4ef1-94d5-7a01de126bbc.png)

### Claude Code - 메인 개발 담당 (복잡한 로직 구현)

**역할**

- 프로젝트의 가장 복잡한 비즈니스 로직 구현
- FastAPI 백엔드 핵심 기능 개발 (추천 알고리즘, 숙소 예약 등등)
- AI 기반 챗봇 및 요약 서비스 구축

**개발 프로세스 (Plan Mode 활용)**

<aside>
💡

Plan Mode는 요청한 작업에 대해 복잡한 로직을 먼저 계획 및 문서화한 이후, 사용자와 함게 확인한 뒤에 개발을 진행합니다.

[1210.mov](images/1210.mov)

</aside>

**1. 전략 수립 단계 (Plan Mode)**
   - 백엔드 배포를 고려했을 때, 해당 알림 기능들에 대한 DB 및 서비스 설계를 어떻게 할까?
   - Claude가 알고리즘 설계, 데이터 구조, 처리 흐름을 상세한 문서로 제시
   - 개발 팀과 함께 검토 및 검증
   - 수정 및 최적화 진행

**2. 구현 단계 (Code Generation)**
   - 검증된 계획을 바탕으로 실제 Python 코드 생성
   - 타입 힌트, 에러 처리, 로깅 포함
   - 구현 이후 실제로 동작하는 지에 대한 테스트 자동화 진행 (MCP 서버 이용)

<aside>
💡

**사용한 MCP 서버 목록**

- **context7**: 최신 기술 문서와 공식 레퍼런스를 자동으로 검색해 정확한 개발 정보를 제공
- **playwright**: 웹 브라우저 자동 제어를 통해 로그인, 데이터 수집, 화면 테스트를 수행
- **sequential-thinking**: 복잡한 문제를 단계별로 구조화해 논리적인 추론 과정을 수행하는 사고 모델
- **notionApi**: 기획 문서, 데이터베이스, 작업 상태를 Notion과 실시간으로 연동
</aside>

---

### Codex - 서브 개발 담당 (코드 검증)

![image.png](images/image%2018.png)

**역할**
- 작성된 코드의 품질 검증
- 성능 최적화 제안, 보안 취약점 검토
- 공식 프롬프트 엔지니어링 문서 기반 개발 진행

**특징**
Codex는 OpenAI가 제공한 공식 프롬프트 엔지니어링 문서를 따라 체계적으로 검증합니다.
- 코드 가독성 및 구조 평가
- 에러 처리의 적절성 확인
- 성능 병목 지점 식별
- 대안 제시 및 최적화 방안 제안

---

### Cursor - 문서 자료 작성 및 빠른 수정

![image.png](images/image%2019.png)

**역할**
- Notion 문서 작성 및 정리
- Github 커밋 메시지 자동 생성
- 단순 오류 수정 (자동 Tab 기능) 및 버그 패치
- 문서화 작업

```bash
# Refresh+ 개발 일지 - 2024년 12월 7일 (토요일)

## 📅 개발 일자
**2024년 12월 7일 (토요일)**

---

## 🎯 이번 주 개발 목표

이번 주는 **인증 시스템 완전 구현**과 **사용자 경험 개선**에 집중했습니다.

---

## ✅ 완료된 작업

### 1. 🔐 로그인 인증 시스템 구현

#### 1.1 백엔드 인증 시스템

**구현된 기능:**
- **JWT 기반 인증**: Access Token + Refresh Token 구조
- **룰루랄라 계정 통합 로그인**: Playwright를 사용한 실제 웹사이트 로그인
- **암호화된 비밀번호 저장**: Fernet 대칭키 암호화 (AES-128)
- **세션 관리**: 세션 쿠키 기반 인증 지원
- **계정 보안**: 
  - 5회 실패 시 30분 계정 잠금
  - 실패 시도 추적 및 IP 주소 기록
  - 토큰 만료 시간 관리 (Access: 1시간, Refresh: 7일)

**새로 생성된 파일:**
- `backend/app/routes/auth.py` - 인증 API 엔드포인트
- `backend/app/schemas/auth.py` - 인증 관련 Pydantic 스키마
- `backend/app/services/auth_service.py` - 인증 비즈니스 로직
- `backend/app/services/lulu_lala_session_manager.py` - 룰루랄라 세션 관리
- `backend/app/utils/encryption.py` - 비밀번호 암호화 유틸리티
- `backend/app/utils/jwt.py` - JWT 토큰 생성/검증 유틸리티
```

## 3. Document AI를 통한 임직원 경험 개선

### 연성소 FAQ 기반 RAG (검색증강) 챗봇

**기술구성:**
- **LangChain**: 검색증강 생성(RAG) 파이프라인 구축
- **Chainlit**: 사용자 친화적 챗봇 인터페이스 제공
- OpenAI 모델: 자연스러운 응답 생성

> *현재 AI 챗봇 및 숙소 정보 요약을 위해 GPT-4o mini 모델을 사용중입니다.*
> 


![image.png](images/image%2020.png)

![image.png](images/image%2021.png)

```bash
system_prompt = """당신은 신한은행 임직원을 위한 Refresh Plus 연성소 예약 플랫폼의 고객 지원 챗봇입니다.
아래 참고 자료를 바탕으로 사용자의 질문에 친절하고 정확하게 답변해주세요.

참고 자료:
{context}

답변 시 주의사항:
1. 참고 자료에 있는 정보를 우선적으로 사용하세요
2. 참고 자료에 없는 내용은 "죄송하지만 해당 정보를 찾을 수 없습니다"라고 안내하세요
3. 친절하고 공손한 어투로 답변하세요
4. 필요시 참고 자료의 번호를 인용하세요 (예: [참고 1]에 따르면...)
"""
```

---

## 4. 이미지 및 영상 AI 활용

### Refresh+ 로고 및 아이콘 - 구글 나노바나나 활용

![sol.webp](images/sol.webp)

![Gemini_Generated_Image_9la12p9la12p9la1.png](images/Gemini_Generated_Image_9la12p9la12p9la1.png)

![refresh_plus_app_logo.png](images/refresh_plus_app_logo.png)

<aside>
💡

Using the uploaded character image, create an app logo where this character stands on the left side next to "Refresh+" text. Keep the character's original design and colors. The "Refresh" text uses ocean blue gradient (deep cerulean #006994 to fresh turquoise #40E0D0). The superscript "+" is in sparkling coral orange (#FF7F50) with a glowing effect. Clean white or transparent background. Horizontal layout, balanced composition, modern and professional style.

</aside>

### Refresh+ 시연 영상 - OpenAI Sora (영상) + Suno (음악)

[https://youtu.be/I9QO4UWyW5E?si=zlVasajdozVaA9pu](https://youtu.be/I9QO4UWyW5E?si=zlVasajdozVaA9pu)

<aside>
🖥️

Style: Cinematic commercial, realistic, emotional contrast, smooth transitions
Aspect Ratio: 9:16 (모바일 광고 최적화)
Lighting: 초반은 차가운 사무실 조명 → 후반은 따뜻한 자연광
Music: 초반 긴장감 있는 리듬 → 앱 실행 후 밝고 설레는 여행 음악

✅ 장면 1: 바쁜 은행원 사무실 (도입부 – 현실의 피로)

A realistic office environment inside a modern bank.
The main character is a tired bank clerk, overwhelmed with paperwork, phone calls ringing, coworkers rushing past.
His face shows exhaustion, stress, and emotional burnout.
Cold blue-toned lighting emphasizes fatigue.
Fast-paced motion, slight camera shake to show chaos.

✅ 장면 2: 아이폰으로 앱 실행 (전환 포인트 – 절대 화면 가리지 않기)

The character sits down briefly, sighs deeply, and takes out an iPhone.
He opens the Refresh+ app.

⚠ Critical instruction:
The character’s hand must NOT block or cover the smartphone screen at any moment.
The app UI must be clearly visible to the viewer at all times.

The screen glows warmly as the app launches.
The character’s expression changes from tired → curious → hopeful.
Soft sound effect signals the transition.

✅ 장면 3: 행복한 여행 – 전주 한옥마을 (힐링 시작)

Seamless cinematic transition from the phone screen into reality.
The character is now walking through Jeonju Hanok Village, wearing casual clothes, smiling naturally.

Traditional Korean houses

Warm sunset lighting

Street food stalls

Relaxed walking, light laughter

Emotional release from work stress

The camera follows smoothly from behind, steady and peaceful.

✅ 장면 4: 서울 고급 호텔 (완벽한 마무리 – 성공적인 힐링)

Cut to a luxury hotel in Seoul at night.
The character enters a high-end hotel lobby with grand lighting and glass architecture.

Check-in scene

Wide city skyline through large window

Sitting by the window with a relaxed smile

Holding a drink, enjoying the night view

Mood is calm, elegant, and deeply satisfying.

✅ 엔딩 연출 (브랜드 메시지)

Final shot:
The character looks at the city skyline peacefully.
Fade to black with text:

“From burnout to balance.”
“Your moment of rest starts with Refresh+.”

</aside>

<aside>
🎵

transitions into an upbeat, and a walking bassline, layers of cheerful handclaps and subtle scatting fill the track, evoking the carefree joy of a sunny picnic day, instrumental only, starts with powerful, percussive drums that dominate the intro for 10 seconds, jazzy swing feel with bright horns, playful piano riffs, jazzy

</aside>

### Notion AI

> 위의 기획서가 보다 발표 시 보다 한 눈에 알아보기 쉽게 Notion AI의 도움을 받았습니다.
> 

---

### 결론

- 기존 레거시 시스템에 대하여, 신규 구축에 대한 개발속도 대폭 감소

![image.png](images/image%2022.png)

<aside>
💡

**Perplexity의 분석 결과**에 따르면, **Refresh+는 4-6개월 외부 업체가 개발할 양**으로 예상.

그러나 여러 AI 툴 및 클라우드 기반 서비스 (백엔드, 프론트, DB)이 있어 개발/배포 효율 대폭 상승 체감

</aside>

- 하나가 아닌, 다양한 AI 툴을 서로 “경쟁”시키며 사용하면 품질을 보증하며 좋은 결과를 얻을 수 있었음
    
    > 특히, 코딩 AI 어시스턴트가 해매고 있는 경우, 다른 AI 어시스턴트에게 도움을 요청하면 한번에 해결하는 경우가 다수 있었음.
    > 
- 이제는 AI를 단순한 도구로 사용하는 것 뿐만 아니라, **실제 핵심 개발 엔진**으로 사용할 수 있을 것으로 기대

![refresh_plus_app_logo (1).png](images/refresh_plus_app_logo_(1).png)