#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 호환 동기 스크래핑 모듈
"""
import sys
import os
from typing import Dict, List
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import logging

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

class SyncNaverBlogScraper:
    """동기 네이버 블로그 스크래퍼 (Windows 호환)"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self._init_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self._close_browser()
    
    def _init_browser(self):
        """브라우저 초기화"""
        try:
            logger.info("Initializing Playwright browser...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _close_browser(self):
        """브라우저 종료"""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def scrape_blog(self, url: str) -> Dict:
        """단일 블로그 스크래핑"""
        if not self.context:
            self._init_browser()
        
        page = self.context.new_page()
        
        try:
            logger.info(f"Scraping: {url}")
            
            # 페이지 로드
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # iframe 처리
            content_html = self._handle_iframe(page)
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(content_html, 'html.parser')
            
            # 컨텐츠 추출
            result = {
                'title': self._extract_title(soup),
                'author': self._extract_author(soup),
                'date': self._extract_date(soup),
                'content': self._extract_body(soup),
                'images': self._extract_images(soup),
                'tags': self._extract_tags(soup),
                'url': url
            }
            
            logger.info(f"Successfully scraped: {result['title']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            raise
        finally:
            page.close()
    
    def _handle_iframe(self, page) -> str:
        """iframe 처리 및 컨텐츠 반환"""
        try:
            # mainFrame iframe 대기
            page.wait_for_selector('#mainFrame', timeout=10000)
            
            # iframe으로 전환
            frame = page.frame('mainFrame')
            if frame:
                logger.debug("Switched to mainFrame iframe")
                return frame.content()
            else:
                logger.debug("No iframe found, using main page content")
                return page.content()
                
        except Exception as e:
            logger.debug(f"Iframe handling failed: {e}, using main page content")
            return page.content()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """제목 추출"""
        selectors = [
            '.se-title-text',
            '.se-module-text h1',
            '.pcol1',
            'div.se_title',
            'h3.se-title',
            '.blog_title',
            'h1'
        ]
        
        for selector in selectors:
            title = soup.select_one(selector)
            if title:
                title_text = title.get_text(strip=True)
                if title_text:
                    return title_text
        
        return "제목 없음"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """작성자 추출"""
        selectors = [
            '.nick',
            '.writer',
            '.blog_author',
            'strong.blog_author',
            '.se-module-text .name'
        ]
        
        for selector in selectors:
            author = soup.select_one(selector)
            if author:
                author_text = author.get_text(strip=True)
                if author_text:
                    return author_text
        
        return "작성자 미상"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """작성일 추출"""
        selectors = [
            '.se_publishDate',
            '.date',
            'span.blog_date',
            '.se-module-text .date',
            'time'
        ]
        
        for selector in selectors:
            date = soup.select_one(selector)
            if date:
                date_text = date.get_text(strip=True)
                if date_text:
                    return date_text
        
        return ""
    
    def _extract_body(self, soup: BeautifulSoup) -> str:
        """본문 내용 추출"""
        selectors = [
            'div.se-main-container',
            'div#postViewArea',
            'div.se_component_wrap',
            'div.post-view',
            'article',
            '.blog_content'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                # 스크립트와 스타일 태그 제거
                for script in content(["script", "style"]):
                    script.decompose()
                
                content_text = content.get_text(separator='\n', strip=True)
                if content_text and len(content_text) > 10:
                    return content_text
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict]:
        """이미지 URL 추출"""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            
            if src and not src.startswith('data:') and not src.endswith('.gif'):
                # 상대 경로를 절대 경로로 변환
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://blog.naver.com' + src
                
                images.append({
                    'url': src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width'),
                    'height': img.get('height')
                })
        
        return images
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """태그 추출"""
        tags = []
        
        tag_selectors = [
            '.tag_area a',
            '.post_tag a',
            '.se-module-text .tag',
            '.blog_tag a',
            '[data-tag]'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            
            for tag in tag_elements:
                tag_text = tag.get_text(strip=True)
                if tag_text:
                    if tag_text.startswith('#'):
                        tag_text = tag_text[1:]
                    
                    if tag_text and tag_text not in tags:
                        tags.append(tag_text)
        
        return tags

def scrape_single_blog(url: str, headless: bool = True) -> Dict:
    """단일 블로그 스크래핑 편의 함수"""
    with SyncNaverBlogScraper(headless=headless) as scraper:
        return scraper.scrape_blog(url)

def scrape_multiple_blogs(urls: List[str], headless: bool = True) -> List[Dict]:
    """다중 블로그 스크래핑 편의 함수"""
    results = []
    with SyncNaverBlogScraper(headless=headless) as scraper:
        for url in urls:
            try:
                result = scraper.scrape_blog(url)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                # 실패한 URL에 대해서도 기본 정보 반환
                results.append({
                    'title': f"스크래핑 실패: {url}",
                    'author': '알 수 없음',
                    'date': '',
                    'content': f"오류: {str(e)}",
                    'images': [],
                    'tags': [],
                    'url': url,
                    'error': str(e)
                })
    
    return results