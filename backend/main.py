from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import json
import os
import sys
from datetime import datetime
import uuid
import threading
import concurrent.futures

# Windows 이벤트 루프 정책 설정 (Playwright 호환성)
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.storage.data_storage import DataStorage

app = FastAPI(title="네이버 블로그 스크래퍼 API", version="1.0.0")

# 정적 파일 서빙 설정
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 진행 중인 작업을 저장할 딕셔너리와 스레드 안전성
active_jobs = {}
jobs_lock = threading.Lock()
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)

class ScrapingRequest(BaseModel):
    urls: List[str]
    download_images: bool = True
    output_format: str = "json"
    max_concurrent: int = 3
    headless: bool = True

class ScrapingJob(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: int = 0
    total_urls: int
    completed_urls: int = 0
    failed_urls: int = 0
    results: List[Dict] = []
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

@app.get("/api/status")
async def api_status():
    """API 상태 확인"""
    return {"message": "네이버 블로그 스크래퍼 API", "version": "1.0.0", "status": "running"}

@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 웹 인터페이스"""
    try:
        static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
        print(f"DEBUG: Looking for static file at: {static_file}")
        print(f"DEBUG: File exists: {os.path.exists(static_file)}")
        
        if os.path.exists(static_file):
            with open(static_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                print(f"DEBUG: Successfully read {len(html_content)} characters")
                return HTMLResponse(content=html_content)
        else:
            print("DEBUG: Static file not found")
            return HTMLResponse(content='''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>File Not Found</title></head>
<body><h1>Static file not found</h1><p>Expected location: ''' + static_file + '''</p></body></html>''')
    except Exception as e:
        print(f"DEBUG: Exception in root handler: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Error</title></head>
<body><h1>Error loading interface</h1><p>Error: {str(e)}</p></body></html>''')

@app.post("/scrape", response_model=Dict)
async def start_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """스크래핑 작업 시작"""
    
    if not request.urls:
        raise HTTPException(status_code=400, detail="URLs가 필요합니다")
    
    # 유효한 URL 검증
    from src.scraper.url_parser import NaverBlogURLParser
    parser = NaverBlogURLParser()
    valid_urls = []
    
    for url in request.urls:
        try:
            parser.parse_url(url)
            valid_urls.append(url)
        except ValueError:
            continue
    
    if not valid_urls:
        raise HTTPException(status_code=400, detail="유효한 네이버 블로그 URL이 없습니다")
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 작업 정보 초기화
    job = ScrapingJob(
        job_id=job_id,
        status="pending",
        total_urls=len(valid_urls),
        created_at=datetime.now()
    )
    
    with jobs_lock:
        active_jobs[job_id] = job
    
    # 스레드 기반 백그라운드 스크래핑 실행
    thread_pool.submit(
        execute_scraping_thread,
        job_id, 
        valid_urls, 
        request.download_images,
        request.output_format,
        request.max_concurrent,
        request.headless
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "total_urls": len(valid_urls),
        "message": f"{len(valid_urls)}개 URL 스크래핑을 시작했습니다"
    }

def execute_scraping_thread(job_id: str, urls: List[str], download_images: bool,
                           output_format: str, max_concurrent: int, headless: bool):
    """스레드 기반 스크래핑 실행"""
    from scraper_sync import scrape_single_blog
    import logging
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    with jobs_lock:
        job = active_jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        job.status = "running"
    
    logger.info(f"Starting scraping job {job_id} with {len(urls)} URLs")
    
    try:
        # 각 URL을 순차적으로 처리
        for i, url in enumerate(urls):
            logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
            try:
                # 직접 스크래핑 실행
                result = scrape_single_blog(url, headless=headless)
                
                with jobs_lock:
                    if result:
                        job.results.append(result)
                        job.completed_urls += 1
                        logger.info(f"Successfully scraped: {result.get('title', 'No title')[:50]}...")
                    else:
                        job.failed_urls += 1
                        job.error_message = "스크래핑 결과가 없음"
                        logger.warning(f"No result for URL: {url}")
                        
            except Exception as e:
                with jobs_lock:
                    job.failed_urls += 1
                    error_msg = f"스크래핑 중 예외 발생: {str(e)}"
                    job.error_message = error_msg
                logger.error(f"Error scraping {url}: {e}")
            
            # 진행률 업데이트
            with jobs_lock:
                job.progress = int((i + 1) / len(urls) * 100)
                logger.info(f"Progress: {job.progress}%")
        
        with jobs_lock:
            if job.completed_urls > 0:
                job.status = "completed"
                logger.info(f"Job {job_id} completed successfully with {job.completed_urls} results")
            else:
                job.status = "failed"
                if not job.error_message:
                    job.error_message = "모든 URL 스크래핑 실패"
                logger.error(f"Job {job_id} failed - no successful results")
            
            job.completed_at = datetime.now()
        
    except Exception as e:
        with jobs_lock:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
        logger.error(f"Scraping job {job_id} failed with exception: {e}")
        import traceback
        traceback.print_exc()

async def run_scraping_process(url: str, headless: bool = True) -> Dict:
    """별도 프로세스에서 스크래핑 실행"""
    import subprocess
    import tempfile
    import asyncio
    
    temp_path = None
    try:
        # 임시 출력 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # 독립 스크래핑 스크립트 실행
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "standalone_scraper.py")
        cmd = [sys.executable, script_path, url, "--headless", "--output", temp_path]
        
        print(f"Running command: {' '.join(cmd)}")
        print(f"Working directory: {os.path.dirname(os.path.dirname(__file__))}")
        print(f"Temp file: {temp_path}")
        
        # subprocess.run을 별도 스레드에서 실행 (Windows 호환성)
        def run_subprocess():
            print(f"DEBUG: About to run subprocess with cmd: {cmd}")
            print(f"DEBUG: Working directory: {os.path.dirname(os.path.dirname(__file__))}")
            try:
                # Windows 환경변수 설정
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=os.path.dirname(os.path.dirname(__file__)),
                    env=env,
                    encoding='utf-8'
                )
                print(f"DEBUG: Subprocess completed with returncode: {result.returncode}")
                print(f"DEBUG: Subprocess stdout: {result.stdout[:200] if result.stdout else 'None'}")
                print(f"DEBUG: Subprocess stderr: {result.stderr[:200] if result.stderr else 'None'}")
                return result
            except Exception as e:
                print(f"DEBUG: Subprocess exception: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # 비동기로 subprocess 실행
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await asyncio.get_event_loop().run_in_executor(executor, run_subprocess)
        
        print(f"Process completed with return code: {result.returncode}")
        print(f"STDOUT: {result.stdout if result.stdout else 'None'}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        # 결과 처리
        if result.returncode == 0:
            # 성공 - 파일에서 결과 읽기
            try:
                if os.path.exists(temp_path):
                    print(f"Reading result from: {temp_path}")
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        scraped_result = json.load(f)
                    os.unlink(temp_path)  # 임시 파일 삭제
                    try:
                        print(f"Successfully scraped: {scraped_result.get('title', 'Unknown')[:50]}")
                    except UnicodeEncodeError:
                        print("Successfully scraped: [Title contains special characters]")
                    return scraped_result
                else:
                    error_msg = "Output file not created"
                    print(f"ERROR: {error_msg}")
                    return create_error_result(url, error_msg)
            except Exception as e:
                print(f"ERROR: Failed to read result file: {e}")
                return create_error_result(url, f"Failed to read result: {e}")
        else:
            # 실패 - 에러 메시지 파싱
            error_msg = result.stderr if result.stderr else "Unknown error"
            print(f"ERROR: Scraping process failed with code {result.returncode}: {error_msg}")
            return create_error_result(url, error_msg)
            
    except subprocess.TimeoutExpired:
        print(f"Scraping timeout for {url}")
        return create_error_result(url, "Timeout after 60 seconds")
    except Exception as timeout_e:
        if "timeout" in str(timeout_e).lower():
            print(f"Scraping timeout for {url}")
            return create_error_result(url, "Timeout after 60 seconds")
    except Exception as e:
        print(f"Process execution failed: {e}")
        import traceback
        traceback.print_exc()
        return create_error_result(url, str(e))
    finally:
        # 임시 파일 정리
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                print(f"Cleaned up temp file: {temp_path}")
        except Exception as cleanup_e:
            print(f"Failed to cleanup temp file: {cleanup_e}")

def create_error_result(url: str, error: str) -> Dict:
    """에러 결과 생성"""
    return {
        'title': f"스크래핑 실패: {url}",
        'author': '알 수 없음',
        'date': '',
        'content': f"오류: {error}",
        'images': [],
        'tags': [],
        'url': url,
        'error': error
    }

@app.get("/job/{job_id}", response_model=ScrapingJob)
async def get_job_status(job_id: str):
    """작업 상태 조회"""
    with jobs_lock:
        if job_id not in active_jobs:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
        
        return active_jobs[job_id]

@app.get("/jobs", response_model=List[ScrapingJob])
async def list_jobs():
    """모든 작업 목록 조회"""
    with jobs_lock:
        return list(active_jobs.values())

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """작업 삭제"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
    
    del active_jobs[job_id]
    return {"message": "작업이 삭제되었습니다"}

@app.get("/download/{job_id}")
async def download_results(job_id: str, format: str = "json"):
    """스크래핑 결과 다운로드"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
    
    job = active_jobs[job_id]
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="작업이 완료되지 않았습니다")
    
    if not job.results:
        raise HTTPException(status_code=404, detail="다운로드할 결과가 없습니다")
    
    # 임시 파일 생성
    temp_dir = "temp_downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    if format == "json":
        filename = f"scraping_results_{job_id}.json"
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(job.results, f, ensure_ascii=False, indent=2)
        
        return FileResponse(
            filepath,
            media_type="application/json",
            filename=filename
        )
    
    elif format == "csv":
        import pandas as pd
        
        filename = f"scraping_results_{job_id}.csv"
        filepath = os.path.join(temp_dir, filename)
        
        # 결과를 DataFrame으로 변환
        df_data = []
        for result in job.results:
            row = {
                'title': result.get('title', ''),
                'author': result.get('author', ''),
                'date': result.get('date', ''),
                'content': result.get('content', ''),
                'blog_id': result.get('blog_id', ''),
                'log_no': result.get('log_no', ''),
                'image_count': len(result.get('images', [])),
                'tags': ', '.join(result.get('tags', []))
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return FileResponse(
            filepath,
            media_type="text/csv",
            filename=filename
        )
    
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 형식입니다")

@app.get("/stats")
async def get_stats():
    """전체 통계 조회"""
    storage = DataStorage()
    all_posts = storage.get_all_posts()
    
    total_posts = len(all_posts)
    total_images = sum(len(post.get('images', [])) for post in all_posts)
    
    # 최근 스크래핑된 포스트들
    recent_posts = sorted(all_posts, key=lambda x: x.get('scraped_at', ''), reverse=True)[:5]
    
    return {
        "total_posts": total_posts,
        "total_images": total_images,
        "active_jobs": len([job for job in active_jobs.values() if job.status == "running"]),
        "recent_posts": [
            {
                "title": post.get('title', ''),
                "author": post.get('author', ''),
                "scraped_at": post.get('scraped_at', '')
            }
            for post in recent_posts
        ]
    }

@app.post("/scrape-sync")
async def scrape_sync(request: ScrapingRequest):
    """동기적 즉시 응답 스크래핑 엔드포인트"""
    if not request.urls:
        raise HTTPException(status_code=400, detail="URLs가 필요합니다")
    
    # 유효한 URL 검증
    from src.scraper.url_parser import NaverBlogURLParser
    parser = NaverBlogURLParser()
    valid_urls = []
    
    for url in request.urls:
        try:
            parser.parse_url(url)
            valid_urls.append(url)
        except ValueError:
            continue
    
    if not valid_urls:
        raise HTTPException(status_code=400, detail="유효한 네이버 블로그 URL이 없습니다")
    
    from scraper_sync import scrape_single_blog
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    results = []
    errors = []
    
    try:
        for i, url in enumerate(valid_urls):
            logger.info(f"Processing URL {i+1}/{len(valid_urls)}: {url}")
            try:
                result = scrape_single_blog(url, headless=request.headless)
                if result:
                    results.append(result)
                    logger.info(f"Successfully scraped: {result.get('title', 'No title')[:50]}...")
                else:
                    errors.append(f"스크래핑 결과가 없음: {url}")
                    
            except Exception as e:
                error_msg = f"스크래핑 실패 {url}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            "success": len(results) > 0,
            "total_urls": len(valid_urls),
            "successful_urls": len(results),
            "failed_urls": len(errors),
            "results": results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Sync scraping failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"스크래핑 중 오류 발생: {str(e)}")

@app.post("/test-scrape") 
async def test_scrape(request: Dict):
    """간단한 테스트용 엔드포인트 - 비동기 스크래핑 사용"""
    url = request.get('url')
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        from scraper_async import scrape_single_blog_async
        
        # 유효한 URL 검증
        from src.scraper.url_parser import NaverBlogURLParser
        parser = NaverBlogURLParser()
        
        try:
            parser.parse_url(url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 네이버 블로그 URL: {str(e)}")
        
        # 비동기 스크래핑 실행
        result = await scrape_single_blog_async(url, headless=True)
        
        if result and not result.get('error'):
            return {
                "success": True,
                "total_urls": 1,
                "successful_urls": 1,
                "failed_urls": 0,
                "results": [result],
                "errors": []
            }
        else:
            return {
                "success": False,
                "total_urls": 1,
                "successful_urls": 0,
                "failed_urls": 1,
                "results": [],
                "errors": [result.get('error', '알 수 없는 오류')]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)