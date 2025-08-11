#!/usr/bin/env python3
"""
비동기 스크래퍼 테스트
"""
import asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_async_scraper():
    from scraper_async import scrape_single_blog_async
    
    url = "https://blog.naver.com/kseta-inc/223963467411"
    print(f"Testing async scraper with: {url}")
    
    result = await scrape_single_blog_async(url, headless=True)
    
    print(f"\nResults:")
    print(f"Title: {result.get('title', 'No title')}")
    print(f"Author: {result.get('author', 'No author')}")
    print(f"Content length: {len(result.get('content', ''))}")
    print(f"Images count: {len(result.get('images', []))}")
    print(f"Error: {result.get('error', 'No error')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_async_scraper())