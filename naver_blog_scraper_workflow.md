# 네이버 블로그 컨텐츠 추출 시스템 구현 워크플로우

## 🎯 프로젝트 개요
네이버 블로그 URL을 입력받아 해당 블로그의 글과 이미지를 자동으로 추출하고 저장하는 시스템 구현

## 📋 요구사항 분석
- **입력**: 네이버 블로그 URL (blog.naver.com 또는 m.blog.naver.com)
- **출력**: 블로그 제목, 본문 내용, 이미지 파일, 메타데이터
- **저장 형식**: JSON, CSV, 또는 데이터베이스
- **성능 요구사항**: Rate limiting, 에러 처리, 재시도 로직

## 🏗️ 시스템 아키텍처

### 기술 스택 선택
```
Primary Stack:
- Language: Python 3.8+
- Web Scraping: Selenium WebDriver 또는 Playwright
- HTML Parsing: BeautifulSoup4
- HTTP Requests: requests, aiohttp (비동기)
- Data Storage: SQLite, JSON
- Image Processing: Pillow
- Testing: pytest, unittest
```

### Alternative Stack (JavaScript):
```
- Language: Node.js
- Web Scraping: Puppeteer, Playwright
- HTML Parsing: Cheerio
- HTTP Requests: axios
- Data Storage: MongoDB, JSON
- Testing: Jest, Mocha
```

## 📅 구현 단계별 워크플로우

### Phase 1: 프로젝트 초기 설정 (Day 1)
#### 1.1 프로젝트 구조 생성
```
naver_blog_scraper/
├── src/
│   ├── __init__.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── blog_scraper.py
│   │   ├── url_parser.py
│   │   └── content_extractor.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── file_storage.py
│   │   └── database_storage.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py
│   │   └── error_handler.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   └── test_storage.py
├── data/
│   ├── images/
│   └── exports/
├── requirements.txt
├── setup.py
├── README.md
└── .env.example
```

#### 1.2 필수 라이브러리 설치
```python
# requirements.txt
selenium==4.15.0
beautifulsoup4==4.12.2
requests==2.31.0
Pillow==10.1.0
python-dotenv==1.0.0
lxml==4.9.3
aiohttp==3.9.0
playwright==1.40.0
pandas==2.1.3
sqlite3
pytest==7.4.3
```

### Phase 2: URL 파싱 및 검증 모듈 (Day 2)
#### 2.1 URL Parser 구현
```python
# src/scraper/url_parser.py
import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional

class NaverBlogURLParser:
    """네이버 블로그 URL 파싱 및 검증"""
    
    VALID_DOMAINS = ['blog.naver.com', 'm.blog.naver.com']
    URL_PATTERNS = {
        'pc': r'https?://blog\.naver\.com/([^/]+)/(\d+)',
        'mobile': r'https?://m\.blog\.naver\.com/([^/]+)/(\d+)',
        'post_view': r'https?://blog\.naver\.com/PostView\.naver\?blogId=([^&]+)&logNo=(\d+)'
    }
    
    def __init__(self):
        self.blog_id = None
        self.log_no = None
        
    def parse_url(self, url: str) -> Dict[str, str]:
        """URL을 파싱하여 blog_id와 log_no 추출"""
        parsed = urlparse(url)
        
        if parsed.netloc not in self.VALID_DOMAINS:
            raise ValueError(f"Invalid domain: {parsed.netloc}")
            
        # URL 패턴 매칭
        for pattern_name, pattern in self.URL_PATTERNS.items():
            match = re.match(pattern, url)
            if match:
                self.blog_id = match.group(1)
                self.log_no = match.group(2)
                break
                
        if not self.blog_id or not self.log_no:
            # Query parameter 방식 처리
            if 'PostView' in parsed.path:
                params = parse_qs(parsed.query)
                self.blog_id = params.get('blogId', [None])[0]
                self.log_no = params.get('logNo', [None])[0]
                
        if not self.blog_id or not self.log_no:
            raise ValueError("Unable to parse blog URL")
            
        return {
            'blog_id': self.blog_id,
            'log_no': self.log_no,
            'normalized_url': f"https://blog.naver.com/{self.blog_id}/{self.log_no}"
        }
```

### Phase 3: 컨텐츠 추출 엔진 구현 (Day 3-4)
#### 3.1 Selenium 기반 동적 컨텐츠 추출
```python
# src/scraper/content_extractor.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        
        return webdriver.Chrome(options=options)
        
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
```

#### 3.2 Playwright 대안 구현 (더 빠른 성능)
```python
# src/scraper/playwright_extractor.py
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, List

class PlaywrightBlogExtractor:
    """Playwright를 사용한 비동기 컨텐츠 추출"""
    
    async def extract_content(self, url: str) -> Dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            await page.goto(url, wait_until='networkidle')
            
            # iframe 처리
            try:
                frame = page.frame('mainFrame')
                if frame:
                    content = await frame.content()
                else:
                    content = await page.content()
            except:
                content = await page.content()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            result = {
                'title': self._extract_title(soup),
                'content': self._extract_body(soup),
                'images': self._extract_images(soup)
            }
            
            await browser.close()
            return result
```

### Phase 4: 이미지 다운로드 및 저장 (Day 5)
#### 4.1 이미지 다운로더 구현
```python
# src/scraper/image_downloader.py
import os
import requests
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse, unquote
from typing import List, Dict
import hashlib

class ImageDownloader:
    """이미지 다운로드 및 저장"""
    
    def __init__(self, save_dir: str = "data/images"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        
    def download_images(self, images: List[Dict], blog_id: str, log_no: str) -> List[Dict]:
        """이미지 다운로드 및 로컬 저장"""
        saved_images = []
        blog_dir = os.path.join(self.save_dir, f"{blog_id}_{log_no}")
        os.makedirs(blog_dir, exist_ok=True)
        
        for idx, img_info in enumerate(images):
            try:
                response = requests.get(img_info['url'], timeout=10)
                if response.status_code == 200:
                    # 이미지 파일명 생성
                    ext = self._get_extension(img_info['url'])
                    filename = f"image_{idx:03d}{ext}"
                    filepath = os.path.join(blog_dir, filename)
                    
                    # 이미지 저장 및 최적화
                    img = Image.open(BytesIO(response.content))
                    
                    # 이미지 크기 최적화 (선택사항)
                    if img.width > 1920:
                        img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                        
                    img.save(filepath, optimize=True, quality=85)
                    
                    saved_images.append({
                        'original_url': img_info['url'],
                        'local_path': filepath,
                        'alt': img_info.get('alt', ''),
                        'size': os.path.getsize(filepath)
                    })
                    
            except Exception as e:
                print(f"Failed to download image: {e}")
                
        return saved_images
        
    def _get_extension(self, url: str) -> str:
        """URL에서 파일 확장자 추출"""
        path = urlparse(url).path
        ext = os.path.splitext(path)[1]
        return ext if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'] else '.jpg'
```

### Phase 5: 데이터 저장 및 Export (Day 6)
#### 5.1 다양한 형식으로 데이터 저장
```python
# src/storage/data_storage.py
import json
import csv
import sqlite3
from datetime import datetime
from typing import Dict, List
import pandas as pd

class DataStorage:
    """추출된 데이터 저장 관리"""
    
    def __init__(self, db_path: str = "data/blog_data.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blog_id TEXT,
                log_no TEXT,
                title TEXT,
                author TEXT,
                date TEXT,
                content TEXT,
                images TEXT,
                tags TEXT,
                scraped_at TIMESTAMP,
                UNIQUE(blog_id, log_no)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def save_to_json(self, data: Dict, filepath: str):
        """JSON 형식으로 저장"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def save_to_csv(self, data: List[Dict], filepath: str):
        """CSV 형식으로 저장"""
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
    def save_to_database(self, data: Dict):
        """데이터베이스에 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO blog_posts 
            (blog_id, log_no, title, author, date, content, images, tags, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('blog_id'),
            data.get('log_no'),
            data.get('title'),
            data.get('author'),
            data.get('date'),
            data.get('content'),
            json.dumps(data.get('images', [])),
            json.dumps(data.get('tags', [])),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
    def export_to_markdown(self, data: Dict, filepath: str):
        """Markdown 형식으로 export"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {data.get('title', '제목 없음')}\n\n")
            f.write(f"**작성자**: {data.get('author', '알 수 없음')}\n")
            f.write(f"**작성일**: {data.get('date', '날짜 없음')}\n\n")
            f.write("---\n\n")
            f.write(data.get('content', ''))
            
            if data.get('images'):
                f.write("\n\n## 이미지\n\n")
                for img in data['images']:
                    f.write(f"![{img.get('alt', '')}]({img.get('local_path', '')})\n")
```

### Phase 6: Rate Limiting 및 에러 처리 (Day 7)
#### 6.1 Rate Limiter 구현
```python
# src/utils/rate_limiter.py
import time
from functools import wraps
from typing import Callable
import random

class RateLimiter:
    """요청 속도 제한"""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        
    def wait(self):
        """요청 간 대기"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 랜덤 지연 시간
        delay = random.uniform(self.min_delay, self.max_delay)
        
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
            
        self.last_request_time = time.time()
        
def rate_limit(min_delay: float = 1.0, max_delay: float = 3.0):
    """데코레이터 방식 rate limiting"""
    def decorator(func: Callable):
        limiter = RateLimiter(min_delay, max_delay)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

#### 6.2 에러 처리 및 재시도 로직
```python
# src/utils/error_handler.py
import time
from functools import wraps
from typing import Callable, Tuple, Type
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetryHandler:
    """재시도 로직 처리"""
    
    @staticmethod
    def retry(
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """재시도 데코레이터"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                attempt = 1
                current_delay = delay
                
                while attempt <= max_attempts:
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        if attempt == max_attempts:
                            logger.error(f"Max attempts reached for {func.__name__}: {e}")
                            raise
                            
                        logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                        attempt += 1
                        
            return wrapper
        return decorator
```

### Phase 7: 메인 애플리케이션 통합 (Day 8)
#### 7.1 통합 스크래퍼 클래스
```python
# src/main_scraper.py
from scraper.url_parser import NaverBlogURLParser
from scraper.content_extractor import NaverBlogContentExtractor
from scraper.image_downloader import ImageDownloader
from storage.data_storage import DataStorage
from utils.rate_limiter import rate_limit
from utils.error_handler import RetryHandler
import logging

class NaverBlogScraper:
    """네이버 블로그 스크래퍼 메인 클래스"""
    
    def __init__(self, headless: bool = True):
        self.url_parser = NaverBlogURLParser()
        self.content_extractor = NaverBlogContentExtractor(headless)
        self.image_downloader = ImageDownloader()
        self.storage = DataStorage()
        self.logger = logging.getLogger(__name__)
        
    @RetryHandler.retry(max_attempts=3, delay=2.0)
    @rate_limit(min_delay=2.0, max_delay=5.0)
    def scrape_blog(self, url: str) -> Dict:
        """블로그 스크래핑 실행"""
        try:
            # URL 파싱
            url_info = self.url_parser.parse_url(url)
            self.logger.info(f"Scraping blog: {url_info['blog_id']}/{url_info['log_no']}")
            
            # 컨텐츠 추출
            content = self.content_extractor.extract_content(url_info['normalized_url'])
            
            # 이미지 다운로드
            if content.get('images'):
                downloaded_images = self.image_downloader.download_images(
                    content['images'],
                    url_info['blog_id'],
                    url_info['log_no']
                )
                content['images'] = downloaded_images
                
            # 메타데이터 추가
            content.update(url_info)
            
            # 데이터 저장
            self.storage.save_to_database(content)
            self.storage.save_to_json(
                content, 
                f"data/exports/{url_info['blog_id']}_{url_info['log_no']}.json"
            )
            
            self.logger.info(f"Successfully scraped: {content.get('title')}")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to scrape {url}: {e}")
            raise
            
    def scrape_multiple(self, urls: List[str]) -> List[Dict]:
        """여러 블로그 포스트 스크래핑"""
        results = []
        for url in urls:
            try:
                result = self.scrape_blog(url)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}")
                continue
                
        return results
        
    def __del__(self):
        """리소스 정리"""
        if hasattr(self, 'content_extractor'):
            self.content_extractor.driver.quit()
```

### Phase 8: 테스트 코드 작성 (Day 9)
#### 8.1 단위 테스트
```python
# tests/test_scraper.py
import pytest
from src.scraper.url_parser import NaverBlogURLParser
from src.scraper.content_extractor import NaverBlogContentExtractor

class TestURLParser:
    def test_parse_standard_url(self):
        parser = NaverBlogURLParser()
        result = parser.parse_url("https://blog.naver.com/test_blog/123456789")
        assert result['blog_id'] == 'test_blog'
        assert result['log_no'] == '123456789'
        
    def test_parse_mobile_url(self):
        parser = NaverBlogURLParser()
        result = parser.parse_url("https://m.blog.naver.com/test_blog/123456789")
        assert result['blog_id'] == 'test_blog'
        assert result['log_no'] == '123456789'
        
    def test_invalid_url(self):
        parser = NaverBlogURLParser()
        with pytest.raises(ValueError):
            parser.parse_url("https://invalid-site.com/blog")

class TestContentExtractor:
    @pytest.mark.integration
    def test_extract_content(self):
        extractor = NaverBlogContentExtractor(headless=True)
        # 실제 블로그 URL로 테스트 (테스트용 블로그 필요)
        content = extractor.extract_content("https://blog.naver.com/test_blog/test_post")
        
        assert 'title' in content
        assert 'content' in content
        assert 'images' in content
```

### Phase 9: CLI 인터페이스 구현 (Day 10)
```python
# cli.py
import argparse
import sys
from src.main_scraper import NaverBlogScraper

def main():
    parser = argparse.ArgumentParser(description='네이버 블로그 스크래퍼')
    parser.add_argument('url', help='네이버 블로그 URL')
    parser.add_argument('--output', '-o', default='json', 
                       choices=['json', 'csv', 'markdown'],
                       help='출력 형식')
    parser.add_argument('--no-images', action='store_true',
                       help='이미지 다운로드 건너뛰기')
    parser.add_argument('--headless', action='store_true',
                       help='헤드리스 모드로 실행')
    
    args = parser.parse_args()
    
    scraper = NaverBlogScraper(headless=args.headless)
    
    try:
        result = scraper.scrape_blog(args.url)
        print(f"✅ 스크래핑 완료: {result.get('title')}")
        print(f"📝 본문 길이: {len(result.get('content', ''))} 자")
        print(f"🖼️ 이미지 수: {len(result.get('images', []))}")
        
    except Exception as e:
        print(f"❌ 스크래핑 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 🚀 실행 방법

### 설치
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치 (Playwright 사용시)
playwright install chromium
```

### 기본 사용법
```bash
# 단일 블로그 포스트 스크래핑
python cli.py "https://blog.naver.com/example/123456789"

# JSON으로 저장
python cli.py "https://blog.naver.com/example/123456789" --output json

# 이미지 제외하고 스크래핑
python cli.py "https://blog.naver.com/example/123456789" --no-images

# 헤드리스 모드
python cli.py "https://blog.naver.com/example/123456789" --headless
```

### Python 코드에서 사용
```python
from src.main_scraper import NaverBlogScraper

# 스크래퍼 초기화
scraper = NaverBlogScraper(headless=True)

# 단일 블로그 스크래핑
result = scraper.scrape_blog("https://blog.naver.com/example/123456789")

# 여러 블로그 스크래핑
urls = [
    "https://blog.naver.com/example1/111111111",
    "https://blog.naver.com/example2/222222222"
]
results = scraper.scrape_multiple(urls)
```

## ⚠️ 주의사항

### 법적/윤리적 고려사항
1. **저작권**: 스크래핑한 컨텐츠의 저작권은 원작자에게 있음
2. **개인정보**: 개인정보가 포함된 데이터 수집 주의
3. **서비스 약관**: 네이버 서비스 이용약관 준수
4. **robots.txt**: 웹사이트의 크롤링 정책 확인

### 기술적 고려사항
1. **Rate Limiting**: 과도한 요청으로 IP 차단 방지
2. **User-Agent**: 적절한 User-Agent 설정
3. **동적 컨텐츠**: JavaScript 렌더링 대기 시간 필요
4. **네트워크 에러**: 재시도 로직 및 예외 처리

## 📊 성능 최적화

### 비동기 처리 (고급)
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def scrape_async(urls: List[str]):
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, scraper.scrape_blog, url)
            for url in urls
        ]
        return await asyncio.gather(*tasks)
```

### 캐싱 전략
- 이미 스크래핑한 URL 추적
- 이미지 중복 다운로드 방지
- 데이터베이스 인덱싱

## 🔧 확장 가능성

### 추가 기능 구현 아이디어
1. **댓글 추출**: 블로그 댓글 스크래핑
2. **통계 분석**: 블로그 통계 정보 수집
3. **카테고리별 수집**: 특정 카테고리 전체 포스트 수집
4. **스케줄링**: 정기적인 업데이트 확인
5. **API 서버**: RESTful API로 제공
6. **웹 인터페이스**: Flask/FastAPI 기반 웹 UI

## 📝 문서화 및 유지보수

### 로깅 설정
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
```

### 모니터링
- 스크래핑 성공/실패율
- 평균 처리 시간
- 에러 발생 패턴
- 리소스 사용량

## 🎯 품질 보증

### 테스트 커버리지
- 단위 테스트: 80% 이상
- 통합 테스트: 주요 플로우
- E2E 테스트: 실제 블로그 URL

### CI/CD 파이프라인
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/
```

## 📚 참고 자료
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Playwright Python](https://playwright.dev/python/)
- [네이버 robots.txt](https://blog.naver.com/robots.txt)