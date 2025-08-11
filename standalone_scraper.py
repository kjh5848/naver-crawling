#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
독립 실행 스크래핑 스크립트 - 프로세스 분리 실행용
"""
import sys
import json
import argparse
import os

# Windows 콘솔 인코딩 설정
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.environ["PYTHONIOENCODING"] = "utf-8"

from backend.scraper_sync import scrape_single_blog

def main():
    parser = argparse.ArgumentParser(description="Naver Blog Scraper")
    parser.add_argument("url", help="Blog URL to scrape")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        # 스크래핑 실행
        result = scrape_single_blog(args.url, args.headless)
        
        # 결과 출력
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result_json)
            print(f"SUCCESS:Results saved to {args.output}")
        else:
            print(f"SUCCESS:{result_json}")
            
    except Exception as e:
        error_result = {
            'title': f"스크래핑 실패: {args.url}",
            'author': '알 수 없음',
            'date': '',
            'content': f"오류: {str(e)}",
            'images': [],
            'tags': [],
            'url': args.url,
            'error': str(e)
        }
        error_json = json.dumps(error_result, ensure_ascii=False, indent=2)
        print(f"ERROR:{error_json}")
        sys.exit(1)

if __name__ == "__main__":
    main()