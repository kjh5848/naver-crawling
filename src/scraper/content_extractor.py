from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from typing import Dict, List

class NaverBlogContentExtractor:
    """네이버 블로그 컨텐츠 추출기"""
    
    def __init__(self, headless: bool = True):
        self.driver = self._setup_driver(headless)
        
    def _setup_driver(self, headless: bool) -> webdriver.Chrome:
        """Selenium WebDriver 설정"""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
        
    def extract_content(self, url: str) -> Dict:
        """블로그 컨텐츠 추출"""
        self.driver.get(url)
        
        # iframe 처리 (네이버 블로그는 iframe 사용)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "mainFrame"))
            )
            self.driver.switch_to.frame("mainFrame")
        except:
            pass  # 일부 블로그는 iframe을 사용하지 않음
            
        # 페이지 로딩 대기
        time.sleep(2)
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        content = {
            'title': self._extract_title(soup),
            'author': self._extract_author(soup),
            'date': self._extract_date(soup),
            'content': self._extract_body(soup),
            'images': self._extract_images(soup),
            'tags': self._extract_tags(soup)
        }
        
        return content
        
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """제목 추출"""
        selectors = [
            '.se-title-text',  # 스마트에디터 3.0
            '.pcol1',          # 구버전
            'div.se_title',    # 스마트에디터 2.0
            'h3.se-title'      # 대체 선택자
        ]
        
        for selector in selectors:
            title = soup.select_one(selector)
            if title:
                return title.get_text(strip=True)
        return "제목 없음"
        
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """작성자 추출"""
        selectors = [
            '.nick',
            '.writer',
            'strong.blog_author'
        ]
        
        for selector in selectors:
            author = soup.select_one(selector)
            if author:
                return author.get_text(strip=True)
        return "작성자 미상"
        
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """작성일 추출"""
        selectors = [
            '.se_publishDate',
            '.date',
            'span.blog_date'
        ]
        
        for selector in selectors:
            date = soup.select_one(selector)
            if date:
                return date.get_text(strip=True)
        return ""
        
    def _extract_body(self, soup: BeautifulSoup) -> str:
        """본문 내용 추출"""
        selectors = [
            'div.se-main-container',  # 스마트에디터 3.0
            'div#postViewArea',       # 구버전
            'div.se_component_wrap'   # 스마트에디터 2.0
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                # 텍스트만 추출
                return content.get_text(separator='\n', strip=True)
        return ""
        
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict]:
        """이미지 URL 추출"""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and not src.startswith('data:'):
                images.append({
                    'url': src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
                
        return images
        
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """태그 추출"""
        tags = []
        tag_elements = soup.select('.tag_area a, .post_tag a')
        
        for tag in tag_elements:
            tag_text = tag.get_text(strip=True)
            if tag_text and not tag_text.startswith('#'):
                tags.append(tag_text)
            elif tag_text.startswith('#'):
                tags.append(tag_text[1:])
                
        return tags
        
    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()