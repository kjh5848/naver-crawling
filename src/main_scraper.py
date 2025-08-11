import os
import logging
from typing import Dict, List
from .scraper.url_parser import NaverBlogURLParser
from .scraper.content_extractor import NaverBlogContentExtractor
from .scraper.image_downloader import ImageDownloader
from .storage.data_storage import DataStorage
from .utils.rate_limiter import rate_limit
from .utils.error_handler import RetryHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class NaverBlogScraper:
    """네이버 블로그 스크래퍼 메인 클래스"""
    
    def __init__(self, headless: bool = True, download_images: bool = True):
        self.url_parser = NaverBlogURLParser()
        self.content_extractor = NaverBlogContentExtractor(headless)
        self.image_downloader = ImageDownloader() if download_images else None
        self.storage = DataStorage()
        self.download_images = download_images
        self.logger = logging.getLogger(__name__)
        
    @RetryHandler.retry(max_attempts=3, delay=2.0)
    @rate_limit(min_delay=2.0, max_delay=5.0)
    def scrape_blog(self, url: str, save_to_db: bool = True, save_to_json: bool = True) -> Dict:
        """블로그 스크래핑 실행"""
        try:
            # URL 파싱
            url_info = self.url_parser.parse_url(url)
            self.logger.info(f"Scraping blog: {url_info['blog_id']}/{url_info['log_no']}")
            
            # 컨텐츠 추출
            content = self.content_extractor.extract_content(url_info['normalized_url'])
            
            # 이미지 다운로드
            if self.download_images and content.get('images'):
                downloaded_images = self.image_downloader.download_images(
                    content['images'],
                    url_info['blog_id'],
                    url_info['log_no']
                )
                content['downloaded_images'] = downloaded_images
                
            # 메타데이터 추가
            content.update(url_info)
            
            # 데이터 저장
            if save_to_db:
                self.storage.save_to_database(content)
                
            if save_to_json:
                os.makedirs('data/exports', exist_ok=True)
                json_path = f"data/exports/{url_info['blog_id']}_{url_info['log_no']}.json"
                self.storage.save_to_json(content, json_path)
                
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
        
    def export_to_markdown(self, url: str, output_path: str = None):
        """블로그 포스트를 마크다운으로 export"""
        try:
            content = self.scrape_blog(url, save_to_db=False, save_to_json=False)
            
            if not output_path:
                url_info = self.url_parser.parse_url(url)
                output_path = f"data/exports/{url_info['blog_id']}_{url_info['log_no']}.md"
                
            self.storage.export_to_markdown(content, output_path)
            self.logger.info(f"Exported to markdown: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to export {url}: {e}")
            raise
            
    def close(self):
        """리소스 정리"""
        if hasattr(self, 'content_extractor'):
            self.content_extractor.close()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()