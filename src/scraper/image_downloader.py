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
                # User-Agent 헤더 추가
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(img_info['url'], headers=headers, timeout=10)
                
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
                        
                    # RGBA를 RGB로 변환 (JPEG 저장을 위해)
                    if img.mode in ('RGBA', 'LA'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                        
                    img.save(filepath, optimize=True, quality=85)
                    
                    saved_images.append({
                        'original_url': img_info['url'],
                        'local_path': filepath,
                        'alt': img_info.get('alt', ''),
                        'size': os.path.getsize(filepath)
                    })
                    
            except Exception as e:
                print(f"Failed to download image {img_info['url']}: {e}")
                
        return saved_images
        
    def _get_extension(self, url: str) -> str:
        """URL에서 파일 확장자 추출"""
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        return ext if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'] else '.jpg'