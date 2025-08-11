import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

@dataclass
class ScrapingConfig:
    """스크래핑 관련 설정"""
    # Rate Limiting
    min_delay: float = 2.0
    max_delay: float = 5.0
    
    # Retry 설정
    max_attempts: int = 3
    retry_delay: float = 2.0
    retry_backoff: float = 2.0
    
    # Timeout 설정
    page_load_timeout: int = 30
    request_timeout: int = 10
    
    # Browser 설정
    headless: bool = True
    window_width: int = 1920
    window_height: int = 1080
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

@dataclass
class StorageConfig:
    """데이터 저장 관련 설정"""
    # 기본 디렉토리
    data_dir: str = "data"
    images_dir: str = "data/images"
    exports_dir: str = "data/exports"
    
    # 데이터베이스
    db_path: str = "data/blog_data.db"
    
    # 파일 형식
    default_format: str = "json"
    
    # 이미지 설정
    download_images: bool = True
    max_image_size: int = 1920
    image_quality: int = 85

@dataclass
class LoggingConfig:
    """로깅 관련 설정"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "scraper.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class ValidationConfig:
    """검증 관련 설정"""
    valid_domains: List[str] = None
    url_patterns: Dict[str, str] = None
    
    def __post_init__(self):
        if self.valid_domains is None:
            self.valid_domains = ['blog.naver.com', 'm.blog.naver.com']
        
        if self.url_patterns is None:
            self.url_patterns = {
                'pc': r'https?://blog\.naver\.com/([^/]+)/(\d+)',
                'mobile': r'https?://m\.blog\.naver\.com/([^/]+)/(\d+)',
                'post_view': r'https?://blog\.naver\.com/PostView\.naver\?blogId=([^&]+)&logNo=(\d+)'
            }

class Settings:
    """전체 설정 관리 클래스"""
    
    def __init__(self):
        # 환경변수에서 설정 로드
        self.scraping = ScrapingConfig(
            min_delay=float(os.getenv('SCRAPING_MIN_DELAY', '2.0')),
            max_delay=float(os.getenv('SCRAPING_MAX_DELAY', '5.0')),
            max_attempts=int(os.getenv('SCRAPING_MAX_ATTEMPTS', '3')),
            headless=os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true',
            user_agent=os.getenv('USER_AGENT', ScrapingConfig().user_agent)
        )
        
        self.storage = StorageConfig(
            data_dir=os.getenv('DATA_DIR', 'data'),
            db_path=os.getenv('DB_PATH', 'data/blog_data.db'),
            download_images=os.getenv('DOWNLOAD_IMAGES', 'true').lower() == 'true'
        )
        
        self.logging = LoggingConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            file_path=os.getenv('LOG_FILE', 'scraper.log')
        )
        
        self.validation = ValidationConfig()
        
        # 디렉토리 생성
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            self.storage.data_dir,
            self.storage.images_dir,
            self.storage.exports_dir,
            os.path.dirname(self.storage.db_path)
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def update_from_dict(self, config_dict: Dict):
        """딕셔너리에서 설정 업데이트"""
        for section, values in config_dict.items():
            if hasattr(self, section):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

# 전역 설정 인스턴스
settings = Settings()