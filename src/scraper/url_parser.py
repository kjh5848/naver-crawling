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