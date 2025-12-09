"""
FAQ 크롤링 배치 작업 (일회성)
- lulu-lala.zzzmobile.co.kr에 로그인
- shbrefresh.interparkb2b.co.kr/intro로 이동
- FAQ 메뉴에 접속하여 모든 FAQ 항목 크롤링
- DB에 저장
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.faq import FAQ
from app.config import settings
from app.utils.logger import get_logger
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from auth.lulu_lala_auth import encrypt_rsa, login_to_lulu_lala, navigate_to_reservation_page

logger = get_logger(__name__)


async def navigate_to_faq_page(page: Page) -> tuple[bool, Page]:
    """
    /board/faq/view 경로로 직접 이동
    
    Args:
        page: Playwright Page 객체
    
    Returns:
        tuple[bool, Page]: (성공 여부, FAQ 페이지 객체)
    """
    try:
        logger.info("Navigating to FAQ page: /board/faq/view")
        
        # 현재 URL에서 기본 도메인 추출
        current_url = page.url
        base_url = current_url.split('/board')[0] if '/board' in current_url else current_url.split('/mypage')[0] if '/mypage' in current_url else "https://shbrefresh.interparkb2b.co.kr"
        
        faq_url = f"{base_url}/board/faq/view"
        logger.info(f"Navigating to: {faq_url}")
        
        await page.goto(faq_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)  # 페이지 로딩 대기
        
        # URL 확인
        final_url = page.url
        logger.info(f"Current URL: {final_url}")
        
        # FAQ 페이지 스크린샷 저장
        await page.screenshot(path="faq_page.png", full_page=True)
        
        return True, page
        
    except Exception as e:
        logger.error(f"Error navigating to FAQ page: {str(e)}", exc_info=True)
        await page.screenshot(path="error_faq_navigation.png", full_page=True)
        return False, page


async def crawl_faq_items_by_category(page: Page, category_name: str) -> List[Dict]:
    """
    특정 카테고리의 FAQ 항목 크롤링
    
    Args:
        page: Playwright Page 객체
        category_name: 카테고리 이름 (예: "신청/배정 문의", "점수문의", "최소문의")
    
    Returns:
        List[Dict]: FAQ 항목 리스트
    """
    try:
        logger.info(f"Crawling FAQ items for category: {category_name}")
        await page.wait_for_timeout(2000)  # 페이지 로딩 대기
        
        faq_items = []
        
        # FAQ 항목 찾기 (dt/dd 구조 또는 다른 구조)
        dt_elements = await page.query_selector_all("dt, [class*='question'], [class*='faq-q']")
        dd_elements = await page.query_selector_all("dd, [class*='answer'], [class*='faq-a']")
        
        if dt_elements and dd_elements:
            logger.info(f"Found {len(dt_elements)} questions and {len(dd_elements)} answers")
            for i, dt in enumerate(dt_elements):
                try:
                    question_text = await dt.inner_text()
                    question_text = question_text.strip()
                    
                    # 대응하는 답변 찾기
                    answer_text = ""
                    if i < len(dd_elements):
                        answer_text = await dd_elements[i].inner_text()
                        answer_text = answer_text.strip()
                    else:
                        # 다음 형제 요소 찾기
                        try:
                            next_sibling = await dt.evaluate_handle("el => el.nextElementSibling")
                            if next_sibling:
                                answer_text = await next_sibling.inner_text()
                                answer_text = answer_text.strip()
                        except:
                            pass
                    
                    if question_text and answer_text:
                        faq_items.append({
                            "question": question_text,
                            "answer": answer_text,
                            "category": category_name,
                            "order": len(faq_items) + 1
                        })
                        logger.info(f"  Found FAQ {len(faq_items)}: Q: {question_text[:50]}...")
                except:
                    continue
        
        # 다른 구조도 시도 (테이블, 리스트 등)
        if not faq_items:
            # FAQ 항목이 포함된 컨테이너 찾기
            container_selectors = [
                "[class*='faq']",
                "[class*='question']",
                "[id*='faq']",
                ".faq-list",
                ".faq-container",
                "tbody",
                "table",
            ]
            
            for selector in container_selectors:
                try:
                    containers = await page.query_selector_all(selector)
                    for container in containers:
                        # 컨테이너 내부의 모든 행 또는 항목 찾기
                        items = await container.query_selector_all("tr, div, li, p")
                        
                        for item in items:
                            try:
                                text = await item.inner_text()
                                text = text.strip()
                                
                                if not text or len(text) < 10:
                                    continue
                                
                                # 질문과 답변이 함께 있는 경우 분리 시도
                                # "Q:" 또는 "질문:" 패턴 찾기
                                import re
                                qa_match = re.search(r'(?:Q[\.:]?\s*|질문[\.:]?\s*)(.+?)(?:A[\.:]?\s*|답변[\.:]?\s*)(.+?)(?=\n\n|$)', text, re.DOTALL)
                                if qa_match:
                                    question = qa_match.group(1).strip()
                                    answer = qa_match.group(2).strip()
                                    if question and answer:
                                        faq_items.append({
                                            "question": question,
                                            "answer": answer,
                                            "category": category_name,
                                            "order": len(faq_items) + 1
                                        })
                                        logger.info(f"  Found FAQ {len(faq_items)}: Q: {question[:50]}...")
                            except:
                                continue
                        
                        if faq_items:
                            break
                except:
                    continue
        
        logger.info(f"Total FAQ items found for category '{category_name}': {len(faq_items)}")
        return faq_items
        
    except Exception as e:
        logger.error(f"Error crawling FAQ items for category '{category_name}': {str(e)}", exc_info=True)
        return []


async def find_and_click_category_button(page: Page, category_name: str) -> bool:
    """
    특정 카테고리 버튼을 찾아 클릭
    
    Args:
        page: Playwright Page 객체
        category_name: 카테고리 이름 (예: "신청/배정 문의", "점수문의", "최소문의")
    
    Returns:
        bool: 성공 여부
    """
    try:
        logger.info(f"Looking for category button: {category_name}")
        await page.wait_for_timeout(1000)
        
        # 카테고리 이름의 다양한 변형 시도
        category_variants = [category_name]
        
        # "최소문의"의 경우 다양한 변형 시도
        if "최소" in category_name:
            category_variants.extend([
                "최소 문의",
                "최소문의",
                "최소",
                "기타문의",
                "기타 문의",
            ])
        
        # 모든 클릭 가능한 요소에서 카테고리 버튼 찾기
        elements = await page.query_selector_all(
            "button, a, [role='button'], [onclick], [class*='btn'], [class*='tab'], [class*='category'], [class*='menu'], li, span"
        )
        
        for element in elements:
            try:
                text = await element.inner_text() if hasattr(element, 'inner_text') else ""
                if not text:
                    text = await element.text_content() if hasattr(element, 'text_content') else ""
                
                href = await element.get_attribute("href") or ""
                class_name = await element.get_attribute("class") or ""
                data_category = await element.get_attribute("data-category") or ""
                title = await element.get_attribute("title") or ""
                id_attr = await element.get_attribute("id") or ""
                
                combined = f"{text} {href} {class_name} {data_category} {title} {id_attr}"
                
                # 카테고리 이름의 모든 변형에 대해 확인
                for variant in category_variants:
                    if variant in combined:
                        logger.info(f"Found category button: {text[:50]} (matched: {variant})")
                        await element.scroll_into_view_if_needed()
                        await element.click()
                        await page.wait_for_timeout(2000)  # FAQ 목록 갱신 대기
                        logger.info(f"✓ Clicked category button: {category_name}")
                        return True
            except:
                continue
        
        # 스크린샷 저장 (디버깅용)
        await page.screenshot(path=f"category_not_found_{category_name.replace('/', '_')}.png", full_page=True)
        logger.warning(f"Category button not found: {category_name}")
        return False
        
    except Exception as e:
        logger.error(f"Error finding category button '{category_name}': {str(e)}")
        return False


async def check_and_click_next_page(page: Page) -> bool:
    """
    다음 페이지 버튼이 있는지 확인하고 클릭
    
    Args:
        page: Playwright Page 객체
    
    Returns:
        bool: 다음 페이지가 있었는지 여부
    """
    try:
        logger.info("Looking for next page button...")
        
        # 먼저 페이지네이션 영역 찾기
        pagination_selectors = [
            "[class*='pagination']",
            "[class*='page']",
            "[id*='pagination']",
            "[id*='page']",
        ]
        
        pagination_container = None
        for selector in pagination_selectors:
            try:
                containers = await page.query_selector_all(selector)
                for container in containers:
                    # 페이지네이션 컨테이너인지 확인 (숫자나 화살표가 있는지)
                    container_text = await container.inner_text()
                    if any(char.isdigit() for char in container_text) or ">" in container_text or "다음" in container_text:
                        pagination_container = container
                        logger.info(f"Found pagination container: {selector}")
                        break
                if pagination_container:
                    break
            except:
                continue
        
        # 페이지네이션 영역 내에서만 찾기
        search_elements = pagination_container.query_selector_all("a, button, [role='button']") if pagination_container else await page.query_selector_all("a, button, [role='button'], [class*='page'], [class*='pagination']")
        
        if pagination_container:
            search_elements = await pagination_container.query_selector_all("a, button, [role='button']")
        else:
            search_elements = await page.query_selector_all("a, button, [role='button'], [class*='page'], [class*='pagination']")
        
        # 방법 1: 페이지 번호 버튼 찾기 (2, 3, 4 등) - 우선순위
        for element in search_elements:
            try:
                text = await element.inner_text() if hasattr(element, 'inner_text') else ""
                if not text:
                    text = await element.text_content() if hasattr(element, 'text_content') else ""
                
                text_clean = text.strip()
                
                # 숫자만 있는 버튼 찾기 (2 이상)
                if text_clean.isdigit() and int(text_clean) >= 2:
                    is_visible = await element.is_visible()
                    class_name = await element.get_attribute("class") or ""
                    
                    # FAQ 카테고리 버튼이 아닌지 확인 (문의가 포함되지 않아야 함)
                    if is_visible and "문의" not in text_clean and "active" not in class_name.lower() and "current" not in class_name.lower():
                        logger.info(f"Found page number button: {text_clean}")
                        await element.scroll_into_view_if_needed()
                        await element.click()
                        await page.wait_for_timeout(2000)  # 페이지 로딩 대기
                        logger.info(f"✓ Clicked page {text_clean} button")
                        return True
            except:
                continue
        
        # 방법 2: 다음 페이지 버튼 찾기 (">", "다음" 등)
        next_page_keywords = [">", "다음", "next"]
        
        for element in search_elements:
            try:
                text = await element.inner_text() if hasattr(element, 'inner_text') else ""
                if not text:
                    text = await element.text_content() if hasattr(element, 'text_content') else ""
                
                href = await element.get_attribute("href") or ""
                class_name = await element.get_attribute("class") or ""
                onclick = await element.get_attribute("onclick") or ""
                
                combined = f"{text} {href} {class_name} {onclick}".lower()
                
                # 다음 페이지 키워드 확인 (하지만 FAQ 카테고리는 제외)
                if any(keyword in combined for keyword in next_page_keywords) and "문의" not in text:
                    is_disabled = await element.get_attribute("disabled")
                    is_visible = await element.is_visible()
                    
                    if is_visible and not is_disabled and "disabled" not in class_name.lower():
                        logger.info(f"Found next page button: {text[:50]}")
                        await element.scroll_into_view_if_needed()
                        await element.click()
                        await page.wait_for_timeout(2000)  # 페이지 로딩 대기
                        logger.info("✓ Clicked next page button")
                        return True
            except:
                continue
        
        logger.info("No next page button found")
        return False
        
    except Exception as e:
        logger.error(f"Error checking next page: {str(e)}")
        return False


async def crawl_faq_items(page: Page) -> List[Dict]:
    """
    FAQ 페이지에서 모든 카테고리의 FAQ 항목 크롤링
    - 각 대분류를 클릭하여 FAQ 목록 갱신
    - "신청/배정 문의"는 2페이지까지 확인
    
    Args:
        page: Playwright Page 객체
    
    Returns:
        List[Dict]: FAQ 항목 리스트
    """
    try:
        logger.info("Crawling FAQ items from all categories...")
        await page.wait_for_timeout(2000)  # 페이지 로딩 대기
        
        all_faq_items = []
        
        # 대분류 목록 - FAQ 페이지의 실제 카테고리만 찾기
        logger.info("Finding FAQ category buttons...")
        await page.wait_for_timeout(1000)
        
        # FAQ 카테고리 버튼 찾기 (FAQ 탭 영역 내에서만)
        # FAQ 관련 키워드가 포함된 카테고리만 필터링
        category_elements = await page.query_selector_all(
            "button, a, [role='button'], [class*='btn'], [class*='tab'], [class*='category']"
        )
        
        available_categories = []
        faq_keywords = ["신청", "배정", "점수", "취소", "최소", "문의"]
        
        for element in category_elements:
            try:
                text = await element.inner_text() if hasattr(element, 'inner_text') else ""
                if not text:
                    text = await element.text_content() if hasattr(element, 'text_content') else ""
                
                text_clean = text.strip()
                
                # FAQ 카테고리인지 확인 (문의가 포함되고, 특정 키워드 포함)
                if text_clean and "문의" in text_clean:
                    # 너무 긴 텍스트는 제외 (메뉴 전체가 아닌 개별 카테고리만)
                    if len(text_clean) < 50 and any(keyword in text_clean for keyword in faq_keywords):
                        if text_clean not in available_categories:
                            available_categories.append(text_clean)
                            logger.info(f"  Found FAQ category: {text_clean}")
            except:
                continue
        
        # 기본 카테고리 목록 (찾지 못한 경우 사용)
        default_categories = ["신청/배정 문의", "점수문의", "취소문의"]
        
        # 사용 가능한 카테고리가 있으면 사용, 없으면 기본값 사용
        if available_categories:
            categories = available_categories
            logger.info(f"Using found FAQ categories: {categories}")
        else:
            categories = default_categories
            logger.info(f"Using default FAQ categories: {categories}")
        
        for category in categories:
            logger.info("=" * 50)
            logger.info(f"Processing category: {category}")
            logger.info("=" * 50)
            
            # 카테고리 버튼 클릭
            category_clicked = await find_and_click_category_button(page, category)
            if not category_clicked:
                logger.warning(f"Failed to click category button: {category}, skipping...")
                continue
            
            # 첫 페이지 FAQ 크롤링
            page_faqs = await crawl_faq_items_by_category(page, category)
            all_faq_items.extend(page_faqs)
            logger.info(f"Found {len(page_faqs)} FAQ items on page 1 for category '{category}'")
            
            # "신청/배정 문의"의 경우 2페이지까지 확인
            if category == "신청/배정 문의":
                logger.info("Checking for page 2 for '신청/배정 문의'...")
                
                # 현재 페이지의 FAQ 개수 확인
                current_count = len(page_faqs)
                logger.info(f"Current page has {current_count} FAQ items")
                
                # 페이지네이션 확인 (여러 방법 시도)
                has_next_page = False
                
                # 방법 1: 다음 페이지 버튼 찾기
                has_next_page = await check_and_click_next_page(page)
                
                # 방법 2: 페이지 번호 버튼 직접 찾기 (2번 버튼)
                if not has_next_page:
                    try:
                        # 페이지 번호가 있는 모든 요소 찾기
                        page_buttons = await page.query_selector_all(
                            "a, button, [class*='page'], [class*='pagination']"
                        )
                        
                        for button in page_buttons:
                            try:
                                text = await button.inner_text() if hasattr(button, 'inner_text') else ""
                                if not text:
                                    text = await button.text_content() if hasattr(button, 'text_content') else ""
                                
                                # "2" 또는 "2페이지" 텍스트가 있는 버튼 찾기
                                if text.strip() == "2" or "2" in text.strip():
                                    is_visible = await button.is_visible()
                                    class_name = await button.get_attribute("class") or ""
                                    
                                    # 활성화된 페이지가 아닌 경우에만 클릭
                                    if is_visible and "active" not in class_name.lower() and "current" not in class_name.lower():
                                        logger.info(f"Found page 2 button: {text}")
                                        await button.scroll_into_view_if_needed()
                                        await button.click()
                                        await page.wait_for_timeout(2000)
                                        has_next_page = True
                                        logger.info("✓ Clicked page 2 button")
                                        break
                            except:
                                continue
                    except:
                        pass
                
                if has_next_page:
                    # 2페이지 FAQ 크롤링
                    page2_faqs = await crawl_faq_items_by_category(page, category)
                    all_faq_items.extend(page2_faqs)
                    logger.info(f"Found {len(page2_faqs)} FAQ items on page 2 for category '{category}'")
                else:
                    logger.info("No page 2 found for '신청/배정 문의'")
        
        logger.info(f"Total FAQ items found across all categories: {len(all_faq_items)}")
        return all_faq_items
        
    except Exception as e:
        logger.error(f"Error crawling FAQ items: {str(e)}", exc_info=True)
        await page.screenshot(path="faq_crawl_error.png", full_page=True)
        return []


async def save_faqs_to_db(faq_items: List[Dict]):
    """
    크롤링한 FAQ 항목을 DB에 저장
    
    Args:
        faq_items: 크롤링한 FAQ 항목 리스트
    """
    async with AsyncSessionLocal() as db:
        try:
            saved_count = 0
            updated_count = 0
            
            # 카테고리별로 그룹화하여 순서 재정렬
            category_groups = {}
            for faq_data in faq_items:
                category = faq_data.get("category", "기타")
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(faq_data)
            
            # 전체 순서 카운터
            global_order = 1
            
            for category, items in category_groups.items():
                logger.info(f"Processing {len(items)} items for category: {category}")
                
                for i, faq_data in enumerate(items, 1):
                    # FAQ ID 생성 (카테고리_순번 형식)
                    category_slug = category.replace("/", "_").replace(" ", "_")
                    faq_id = f"faq_{category_slug}_{i:04d}"
                    
                    # 질문과 답변 텍스트 정리
                    question = faq_data.get("question", "").strip()
                    answer = faq_data.get("answer", "").strip()
                    
                    if not question or not answer:
                        logger.warning(f"Skipping FAQ item: missing question or answer")
                        continue
                    
                    # 기존 FAQ 확인 (질문 텍스트와 카테고리로 중복 체크)
                    existing = await db.execute(
                        select(FAQ).where(
                            FAQ.question == question,
                            FAQ.category == category
                        )
                    )
                    existing_faq = existing.scalar_one_or_none()
                    
                    if existing_faq:
                        # 업데이트
                        existing_faq.answer = answer
                        existing_faq.order = global_order
                        existing_faq.updated_at = datetime.utcnow()
                        db.add(existing_faq)
                        updated_count += 1
                        logger.debug(f"Updated FAQ: [{category}] {question[:50]}...")
                    else:
                        # 새로 생성
                        new_faq = FAQ(
                            id=faq_id,
                            question=question,
                            answer=answer,
                            category=category,
                            order=global_order
                        )
                        db.add(new_faq)
                        saved_count += 1
                        logger.debug(f"Saved FAQ: [{category}] {question[:50]}...")
                    
                    global_order += 1
            
            await db.commit()
            logger.info(f"FAQs - Saved: {saved_count}, Updated: {updated_count}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Database save error: {str(e)}", exc_info=True)
            raise


async def process_faq_crawling(
    username: Optional[str] = None,
    password: Optional[str] = None
) -> Dict:
    """
    FAQ 크롤링 배치 작업 메인 함수
    
    Args:
        username: lulu-lala 로그인 사용자명 (None이면 설정에서 로드)
        password: lulu-lala 로그인 비밀번호 (None이면 설정에서 로드)
    
    Returns:
        Dict: 작업 결과
    """
    # 설정에서 로드 (인자가 없을 경우)
    if username is None:
        username = settings.LULU_LALA_USERNAME
    if password is None:
        password = settings.LULU_LALA_PASSWORD
    
    if not username or not password:
        error_msg = (
            "로그인 정보가 설정되지 않았습니다. "
            ".env 파일에 LULU_LALA_USERNAME과 LULU_LALA_PASSWORD를 설정하세요."
        )
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # RSA 공개키 확인
    rsa_public_key = settings.LULU_LALA_RSA_PUBLIC_KEY
    if not rsa_public_key:
        error_msg = (
            "RSA 공개키가 설정되지 않았습니다. "
            ".env 파일에 LULU_LALA_RSA_PUBLIC_KEY를 설정하세요."
        )
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async with async_playwright() as p:
        browser: Browser = None
        context: BrowserContext = None
        page: Page = None
        
        try:
            logger.info("Starting FAQ crawling batch job...")

            # 브라우저 시작
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',  # Docker/메모리 제한 환경 최적화
                    '--no-sandbox',  # Docker 환경 호환성
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # 단계 1: 로그인
            logger.info("=" * 50)
            logger.info("STEP 1: Logging in to lulu-lala...")
            logger.info("=" * 50)
            login_success = await login_to_lulu_lala(page, username, password, rsa_public_key)
            if not login_success:
                await page.screenshot(path="faq_step1_login_failed.png", full_page=True)
                return {
                    "status": "error",
                    "message": "Login failed",
                    "step": "login",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info("✓ Login successful")
            logger.info(f"Current URL: {page.url}")
            
            # 단계 2: Refresh 아이콘 클릭 후 shbrefresh로 이동
            logger.info("=" * 50)
            logger.info("STEP 2: Navigating to shbrefresh via Refresh icon...")
            logger.info("=" * 50)
            
            nav_success, page = await navigate_to_reservation_page(page, context)
            if not nav_success:
                logger.error("Failed to navigate to shbrefresh page")
                return {
                    "status": "error",
                    "message": "Failed to navigate to shbrefresh page",
                    "step": "navigation",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info(f"✓ Successfully navigated to shbrefresh page: {page.url}")
            
            # 단계 3: FAQ 메뉴로 이동
            logger.info("=" * 50)
            logger.info("STEP 3: Navigating to FAQ page...")
            logger.info("=" * 50)
            
            faq_success, page = await navigate_to_faq_page(page)
            if not faq_success:
                logger.error("Failed to navigate to FAQ page")
                return {
                    "status": "error",
                    "message": "Failed to navigate to FAQ page",
                    "step": "faq_navigation",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info(f"✓ Successfully navigated to FAQ page: {page.url}")
            
            # 단계 4: FAQ 항목 크롤링
            logger.info("=" * 50)
            logger.info("STEP 4: Crawling FAQ items...")
            logger.info("=" * 50)
            
            faq_items = await crawl_faq_items(page)
            
            if not faq_items:
                logger.warning("No FAQ items found")
                return {
                    "status": "warning",
                    "message": "No FAQ items found",
                    "faq_count": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # DB에 저장
            await save_faqs_to_db(faq_items)
            
            logger.info(f"FAQ crawling completed: {len(faq_items)} FAQ items")
            
            return {
                "status": "success",
                "faq_count": len(faq_items),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"FAQ crawling failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
