# 네이버 블로그 스크래퍼

네이버 블로그의 컨텐츠를 자동으로 추출하고 저장하는 Full-Stack 웹 애플리케이션입니다.

## 🚀 주요 기능

- 🌐 **모던 웹 인터페이스**: React + TypeScript 기반의 직관적인 UI
- ⚡ **고성능 스크래핑**: Playwright 기반 Windows 최적화 스크래핑 엔진
- 📊 **실시간 작업 관리**: 백그라운드 작업 처리 및 진행률 모니터링
- 💾 **다양한 저장 형식**: JSON, CSV, Markdown, SQLite 지원
- 🔄 **자동 재시도 로직**: 안정적인 스크래핑을 위한 에러 복구 시스템
- 🛡️ **Rate Limiting**: IP 차단 방지를 위한 자동 속도 제한

## 🎯 빠른 시작

```bash
# 1. 저장소 클론
git clone [repository-url]
cd naver_crawling

# 2. 가상환경 설정
python -m venv venv
venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt
playwright install chromium
cd frontend && npm install && cd ..

# 4. 애플리케이션 실행
python run_web.py
```

웹 브라우저가 자동으로 열리며 http://localhost:3000 에서 사용할 수 있습니다.

## 설치 방법

### 1. 프로젝트 클론 또는 다운로드
```bash
git clone [repository-url]
cd naver_crawling
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### 3. 필요 패키지 설치
```bash
# Python 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치 (Windows 필수)
playwright install chromium

# Frontend 패키지 설치
cd frontend
npm install
cd ..
```

## 사용 방법

### 🌟 웹 애플리케이션 사용 (권장)

#### 원클릭 실행
```bash
python run_web.py
```

이 명령어 하나로:
- ✅ 백엔드 API 서버 자동 시작 (포트 8000)
- ✅ 프론트엔드 웹 서버 자동 시작 (포트 3000)
- ✅ 브라우저에서 자동으로 애플리케이션 열기
- ✅ 포트 충돌 자동 해결

#### 웹 인터페이스 접속
- **메인 페이지**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs
- **테스트 URL**: `https://blog.naver.com/kseta-inc/223963467411`

### 📝 독립 스크래퍼 사용

#### 단일 블로그 스크래핑
```bash
python standalone_scraper.py "https://blog.naver.com/example/123456789" --headless
```

#### 결과 파일로 저장
```bash
python standalone_scraper.py "URL" --headless --output result.json
```

### 🔧 개발자용 API

#### Python에서 직접 사용
```python
from backend.scraper_sync import scrape_single_blog

# 단일 블로그 스크래핑
result = scrape_single_blog("https://blog.naver.com/example/123456789", headless=True)
print(f"제목: {result['title']}")
print(f"작성자: {result['author']}")
print(f"본문 길이: {len(result['content'])} 자")
```

#### REST API 사용
```python
import requests

# 스크래핑 작업 시작
response = requests.post("http://localhost:8000/scrape", json={
    "urls": ["https://blog.naver.com/example/123456789"],
    "headless": True
})
job = response.json()

# 작업 상태 확인
status = requests.get(f"http://localhost:8000/job/{job['job_id']}")
print(status.json())
```

## 🛠️ 개발 환경 설정

### 백엔드 개발 서버
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 개발 서버
```bash
cd frontend
npm run dev
```

### 🐳 Docker 실행 (프로덕션)

#### 전체 스택 실행
```bash
docker-compose up -d
```

#### 개별 서비스 실행
```bash
# 백엔드만 실행
docker-compose up -d backend

# 프론트엔드만 실행  
docker-compose up -d frontend
```

#### Docker 서비스 종료
```bash
docker-compose down
```

### 📱 API 엔드포인트

```bash
# 스크래핑 작업 시작
POST http://localhost:8000/scrape
{
  "urls": ["https://blog.naver.com/example/123456789"],
  "headless": true
}

# 작업 상태 조회
GET http://localhost:8000/job/{job_id}

# 모든 작업 목록
GET http://localhost:8000/jobs

# 통계 조회
GET http://localhost:8000/stats

# 결과 다운로드
GET http://localhost:8000/download/{job_id}?format=json
```

### 🔧 환경 설정

#### 환경 변수 (.env 파일)
```env
# 데이터베이스 설정
DATABASE_PATH=./data/blog_data.db

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE=./logs/scraper.log

# 스크래핑 설정
DEFAULT_CONCURRENT=3
DEFAULT_DELAY=2.0
MAX_ATTEMPTS=3

# 웹 서버 설정
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### 📊 모니터링 및 로깅

#### 로그 파일 위치
```
logs/
├── scraper.log        # 일반 로그
├── errors.log         # 에러 로그
└── performance.log    # 성능 로그
```

#### 실시간 로그 모니터링
```bash
# 일반 로그 실시간 확인
tail -f logs/scraper.log

# 에러 로그 실시간 확인
tail -f logs/errors.log
```

## 프로젝트 구조

```
naver_crawling/
├── backend/                    # FastAPI 백엔드
│   ├── main.py                 # API 서버 및 백그라운드 작업 관리
│   └── scraper_sync.py         # Windows 최적화 Playwright 스크래퍼
├── frontend/                   # React TypeScript 프론트엔드
│   ├── src/
│   │   ├── App.tsx             # 메인 React 컴포넌트
│   │   ├── components/         # UI 컴포넌트
│   │   └── main.tsx            # 애플리케이션 진입점
│   ├── package.json            # 프론트엔드 의존성
│   ├── vite.config.ts          # Vite 빌드 설정
│   └── tailwind.config.js      # Tailwind CSS 설정
├── src/                        # 핵심 스크래핑 모듈
│   ├── scraper/
│   │   ├── url_parser.py       # URL 파싱 및 검증
│   │   ├── content_extractor.py # Selenium 기반 컨텐츠 추출
│   │   └── image_downloader.py  # 이미지 다운로드 및 최적화
│   ├── storage/
│   │   └── data_storage.py     # 다중 형식 데이터 저장 (JSON/CSV/SQLite)
│   ├── utils/
│   │   ├── rate_limiter.py     # Rate limiting 데코레이터
│   │   └── error_handler.py    # 에러 처리 및 재시도 로직
│   └── main_scraper.py         # 메인 스크래퍼 클래스
├── legacy/                     # 레거시 코드 아카이브
│   ├── cli.py                  # 기존 CLI 인터페이스
│   └── example_usage.py        # 사용 예제
├── data/                       # 데이터 저장소
│   ├── images/                 # 다운로드된 이미지
│   ├── exports/                # Export된 파일
│   └── blog_data.db            # SQLite 데이터베이스
├── standalone_scraper.py       # 독립 실행 스크래퍼
├── run_web.py                  # 웹 애플리케이션 통합 런처
├── requirements.txt            # Python 의존성
├── CLAUDE.md                   # Claude Code 가이드
└── README.md                   # 프로젝트 문서
```

## 저장 형식

### JSON 형식
```json
{
  "title": "블로그 제목",
  "author": "작성자",
  "date": "2024-01-01",
  "content": "본문 내용...",
  "images": [...],
  "tags": ["태그1", "태그2"],
  "blog_id": "example",
  "log_no": "123456789"
}
```

### SQLite 데이터베이스
- 테이블명: `blog_posts`
- 자동으로 `data/blog_data.db`에 저장

### Markdown 형식
- 제목, 작성자, 날짜, 본문, 이미지를 포함한 마크다운 파일 생성

## 주의사항

### 법적/윤리적 고려사항
- **저작권**: 스크래핑한 컨텐츠의 저작권은 원작자에게 있습니다
- **개인정보**: 개인정보가 포함된 데이터 수집에 주의하세요
- **서비스 약관**: 네이버 서비스 이용약관을 준수하세요
- **상업적 사용**: 상업적 목적으로 사용 시 법적 문제가 발생할 수 있습니다

### 기술적 고려사항
- **Rate Limiting**: 과도한 요청으로 IP가 차단될 수 있습니다
- **동적 컨텐츠**: 일부 블로그는 JavaScript 렌더링 시간이 필요합니다
- **네트워크 에러**: 네트워크 상태에 따라 실패할 수 있습니다

## 문제 해결

### Windows 환경 이슈
```bash
# Playwright 브라우저 설치
playwright install chromium

# 포트 충돌 해결 (자동으로 처리됨)
python run_web.py  # 자동으로 포트 3000, 8000 정리
```

### 스크래핑 실패
- URL이 올바른지 확인
- 블로그가 비공개 설정되어 있는지 확인
- 테스트 URL로 확인: `https://blog.naver.com/kseta-inc/223963467411`

### 이미지 다운로드 실패
- 네트워크 상태 확인
- `Pillow` 패키지 재설치: `pip install --upgrade Pillow`

### 포트 사용 중 오류
```bash
# Windows에서 포트 사용 프로세스 확인
netstat -aon | findstr :3000
netstat -aon | findstr :8000

# run_web.py가 자동으로 처리하지만 수동으로 종료하려면
taskkill /f /pid [PID]
```

## 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다. 상업적 사용 시 관련 법규를 확인하세요.

## 기여

버그 리포트, 기능 제안, 풀 리퀘스트를 환영합니다.