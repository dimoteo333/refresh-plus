# Refresh Plus RAG 챗봇

FAQ 기반 질의응답 챗봇 시스템

## 기술 스택

- **LangGraph**: 챗봇 워크플로우 관리
- **LangChain**: LLM 통합
- **OpenAI GPT-4o-mini**: 언어 모델
- **ChromaDB**: 벡터 데이터베이스
- **Chainlit**: 채팅 UI
- **HuggingFace Sentence Transformers**: 한국어 임베딩 (`jhgan/ko-sroberta-multitask`)

## 아키텍처

```
사용자 질문
    ↓
Vector Search (ChromaDB)
    ↓
관련 FAQ 검색 (top 3)
    ↓
LangGraph RAG 워크플로우
    ↓
OpenAI GPT-4o-mini
    ↓
답변 생성
```

## 설치 및 설정

### 1. 환경 변수 설정

`.env` 파일에 다음 변수 추가:

```bash
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-...

# 데이터베이스 URL (기존)
DATABASE_URL=sqlite+aiosqlite:///./refresh_plus.db
```

### 2. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

### 3. FAQ 데이터 크롤링

FAQ 크롤러를 실행하여 데이터 수집:

```bash
python batch/run_faq_crawler.py
```

### 4. FAQ 벡터화

크롤링된 FAQ를 벡터화하여 ChromaDB에 저장:

```bash
python batch/run_faq_vectorize.py
```

## 사용 방법

### API 엔드포인트 사용

#### 1. 챗봇 질의응답

```bash
POST /api/chatbot/chat
```

**요청 예시:**

```json
{
  "query": "포인트는 어떻게 회복되나요?"
}
```

**응답 예시:**

```json
{
  "success": true,
  "response": "포인트는 24시간마다 자동으로 회복됩니다...",
  "context": "[참고 1]\n질문: 포인트 회복은 언제 되나요?\n답변: ...",
  "error": null
}
```

#### 2. FAQ 벡터화 (관리자 전용)

```bash
POST /api/chatbot/vectorize
```

모든 FAQ를 벡터화하여 ChromaDB에 저장합니다. 기존 벡터는 초기화됩니다.

**응답 예시:**

```json
{
  "success": 50,
  "failed": 0,
  "total": 50
}
```

#### 3. 챗봇 통계

```bash
GET /api/chatbot/stats
```

**응답 예시:**

```json
{
  "success": true,
  "data": {
    "collection_name": "faq_collection",
    "total_documents": 50
  }
}
```

### Chainlit UI 사용

Chainlit을 사용하여 웹 기반 채팅 UI를 제공할 수 있습니다:

```bash
cd backend
chainlit run chainlit_app.py -w
```

브라우저에서 `http://localhost:8000` 접속하여 채팅 시작.

**Chainlit UI 기능:**

- 실시간 채팅 인터페이스
- 메시지 히스토리
- 참고 자료 표시
- 로딩 인디케이터

## 배치 작업

### Railway Cron 설정

FAQ 크롤링 후 자동으로 벡터화하도록 설정:

#### 1. FAQ 크롤러 (매일 02:00 KST)

```bash
# Cron 스케줄: 0 17 * * * (UTC)
python batch/run_faq_crawler.py
```

#### 2. FAQ 벡터화 (매일 03:00 KST)

```bash
# Cron 스케줄: 0 18 * * * (UTC)
python batch/run_faq_vectorize.py
```

## 커스터마이징

### 1. 임베딩 모델 변경

`app/integrations/vector_store.py` 파일에서 임베딩 모델 변경:

```python
# 기본값: 한국어 특화 모델
model_name="jhgan/ko-sroberta-multitask"

# 다른 모델 예시
# model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

### 2. LLM 모델 변경

`app/services/chatbot_service.py` 파일에서 LLM 모델 변경:

```python
self.llm = ChatOpenAI(
    model="gpt-4o-mini",  # 기본값
    # model="gpt-4",      # 더 정확한 응답
    # model="gpt-3.5-turbo",  # 빠른 응답
    temperature=0.7
)
```

### 3. 검색 결과 개수 조정

`app/services/chatbot_service.py`의 `_retrieve_context` 메서드:

```python
results = self.faq_vector_service.search_similar_faqs(
    query=query,
    n_results=3  # 3개 → 원하는 개수로 변경
)
```

### 4. 프롬프트 커스터마이징

`app/services/chatbot_service.py`의 `_generate_response` 메서드에서 `system_prompt` 수정.

## 테스트

### 로컬 테스트

```bash
# 1. FastAPI 서버 실행
uvicorn app.main:app --reload

# 2. 챗봇 API 테스트
curl -X POST "http://localhost:8000/api/chatbot/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "포인트는 어떻게 회복되나요?"}'

# 3. Chainlit UI 테스트
chainlit run chainlit_app.py
```

### 벡터 검색 테스트

Python 인터프리터에서:

```python
from app.services.faq_vector_service import get_faq_vector_service

service = get_faq_vector_service()

# 검색 테스트
results = service.search_similar_faqs(
    query="포인트 회복",
    n_results=3
)

print(results)
```

## 문제 해결

### ChromaDB 초기화 오류

```bash
# ChromaDB 디렉토리 삭제 후 재생성
rm -rf backend/chroma_db
python batch/run_faq_vectorize.py
```

### OpenAI API 키 오류

`.env` 파일에 올바른 API 키 설정 확인:

```bash
OPENAI_API_KEY=sk-...
```

### 벡터화된 문서가 없음

FAQ 크롤러와 벡터화 배치 작업 순서대로 실행:

```bash
# 1. FAQ 크롤링
python batch/run_faq_crawler.py

# 2. FAQ 벡터화
python batch/run_faq_vectorize.py

# 3. 통계 확인
curl http://localhost:8000/api/chatbot/stats
```

## 향후 개선 사항

- [ ] Turso vector extension 사용 (ChromaDB 대체)
- [ ] 대화 히스토리 관리
- [ ] 사용자별 맞춤 응답
- [ ] 피드백 시스템 (좋아요/싫어요)
- [ ] 멀티턴 대화 지원
- [ ] 카테고리별 필터링
- [ ] 응답 캐싱
- [ ] A/B 테스팅

## 참고 자료

- [LangGraph 문서](https://python.langchain.com/docs/langgraph)
- [Chainlit 문서](https://docs.chainlit.io/)
- [ChromaDB 문서](https://docs.trychroma.com/)
- [OpenAI API 문서](https://platform.openai.com/docs/)
