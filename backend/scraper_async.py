#!/usr/bin/env python3
"""
비동기 네이버 블로그 스크래퍼 - Windows FastAPI 호환성
"""
import asyncio
import sys
import os
import logging
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright
from datetime import datetime

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scrape_single_blog_async(url: str, headless: bool = True) -> dict:
    """
    단일 네이버 블로그 포스트 스크래핑 (비동기)
    """
    logger.info(f"Starting async scraping for: {url}")
    
    async with async_playwright() as p:
        try:
            # 브라우저 시작
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page()
            
            # User-Agent 설정 (봇 차단 방지)
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            # 페이지 로딩
            logger.info("Loading page...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)  # 페이지 로딩 대기
            
            # iframe 감지 및 전환
            iframe = None
            try:
                iframe_element = await page.wait_for_selector("iframe#mainFrame", timeout=10000)
                if iframe_element:
                    iframe = await iframe_element.content_frame()
                    logger.info("Switched to mainFrame iframe")
                else:
                    iframe = page  # iframe이 없으면 메인 페이지 사용
            except Exception as e:
                logger.warning(f"No iframe found, using main page: {e}")
                iframe = page
            
            # URL에서 블로그 ID와 로그 번호 추출
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            
            blog_id = ""
            log_no = ""
            
            if len(path_parts) >= 2:
                blog_id = path_parts[1]
            if len(path_parts) >= 3:
                log_no = path_parts[2]
            
            # Query parameters에서 logNo 추출 (대체 방법)
            if not log_no:
                query_params = parse_qs(parsed_url.query)
                if 'logNo' in query_params:
                    log_no = query_params['logNo'][0]
            
            logger.info(f"Blog ID: {blog_id}, Log No: {log_no}")
            
            # 제목 추출
            title = ""
            title_selectors = [
                ".se-title-text",  # Smart Editor 3.0
                "div.se_title",    # Smart Editor 2.0
                ".pcol1 .title_area",  # 구버전
                ".tit_area .tit",      # 다른 구버전
                "h1",  # 일반적인 제목
            ]
            
            for selector in title_selectors:
                try:
                    element = await iframe.query_selector(selector)
                    if element:
                        title = await element.text_content()
                        title = title.strip() if title else ""
                        if title:
                            logger.info(f"Found title using selector {selector}: {title[:50]}...")
                            break
                except Exception as e:
                    logger.debug(f"Title selector {selector} failed: {e}")
                    continue
            
            if not title:
                title = f"제목을 찾을 수 없음 - {blog_id}"
                logger.warning("Could not extract title")
            
            # 작성자 추출
            author = ""
            author_selectors = [
                ".blog_author",
                ".nick_area .nick",
                ".se-author-text",
                ".author",
                "[class*='author']"
            ]
            
            for selector in author_selectors:
                try:
                    element = await iframe.query_selector(selector)
                    if element:
                        author = await element.text_content()
                        author = author.strip() if author else ""
                        if author:
                            logger.info(f"Found author: {author}")
                            break
                except Exception as e:
                    logger.debug(f"Author selector {selector} failed: {e}")
                    continue
            
            if not author:
                author = blog_id if blog_id else "알 수 없음"
                logger.info(f"Using blog_id as author: {author}")
            
            # 내용 추출
            content = ""
            content_selectors = [
                "div.se-main-container",  # Smart Editor 3.0
                "div.se_component_wrap",  # Smart Editor 2.0
                "div#postViewArea",       # 구버전
                ".post-view",             # 다른 구버전
                "[class*='content']",     # 일반적인 내용
            ]
            
            for selector in content_selectors:
                try:
                    element = await iframe.query_selector(selector)
                    if element:
                        content = await element.text_content()
                        content = content.strip() if content else ""
                        if len(content) > 50:  # 충분한 내용이 있는 경우
                            logger.info(f"Found content using selector {selector}: {len(content)} chars")
                            break
                except Exception as e:
                    logger.debug(f"Content selector {selector} failed: {e}")
                    continue
            
            if not content:
                content = "내용을 추출할 수 없습니다."
                logger.warning("Could not extract content")
            
            # 이미지 URL 추출
            images = []
            try:
                # 다양한 이미지 선택자 시도
                image_selectors = [
                    "img.se-image-resource",  # Smart Editor 3.0
                    "img.se_img",             # Smart Editor 2.0
                    "div#postViewArea img",   # 구버전
                    "img[src*='blogfiles.naver.net']",  # 네이버 이미지 서버
                    "img[src*='pstatic.net']",          # 네이버 정적 파일 서버
                ]
                
                for selector in image_selectors:
                    try:
                        elements = await iframe.query_selector_all(selector)
                        for img in elements:
                            src = await img.get_attribute('src')
                            if src and src.startswith('http'):
                                if src not in images:
                                    images.append(src)
                        if images:
                            logger.info(f"Found {len(images)} images using selector {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Image selector {selector} failed: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error extracting images: {e}")
            
            # 작성일 추출
            date = ""
            date_selectors = [
                ".se_publishDate",
                ".blog_date",
                ".date",
                "[class*='date']"
            ]
            
            for selector in date_selectors:
                try:
                    element = await iframe.query_selector(selector)
                    if element:
                        date = await element.text_content()
                        date = date.strip() if date else ""
                        if date:
                            logger.info(f"Found date: {date}")
                            break
                except Exception as e:
                    logger.debug(f"Date selector {selector} failed: {e}")
                    continue
            
            # 브라우저 종료
            await browser.close()
            
            result = {
                'title': title,
                'author': author,
                'date': date,
                'content': content[:1000] + "..." if len(content) > 1000 else content,  # 내용 제한
                'images': images,
                'tags': [],  # 태그는 구현 생략
                'blog_id': blog_id,
                'log_no': log_no,
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully scraped: {title[:50]}... ({len(images)} images)")
            return result
            
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            import traceback
            traceback.print_exc()
            
            # 브라우저가 열려 있으면 닫기
            try:
                await browser.close()
            except:
                pass
            
            # 에러 결과 반환
            return {
                'title': f'스크래핑 실패: {url}',
                'author': '알 수 없음',
                'date': '',
                'content': f'오류: {str(e)}',
                'images': [],
                'tags': [],
                'blog_id': '',
                'log_no': '',
                'url': url,
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }

# 테스트용 함수
async def test_scraping():
    """테스트용 함수"""
    url = "https://blog.naver.com/kseta-inc/223963467411"
    result = await scrape_single_blog_async(url, headless=True)
    print(f"Title: {result['title']}")
    print(f"Author: {result['author']}")
    print(f"Content length: {len(result['content'])}")
    print(f"Images: {len(result['images'])}")
    return result

if __name__ == "__main__":
    asyncio.run(test_scraping())