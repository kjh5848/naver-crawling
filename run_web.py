#!/usr/bin/env python3
"""
네이버 블로그 스크래퍼 웹 애플리케이션 실행 스크립트
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def run_backend():
    """백엔드 서버 실행"""
    print("[시작] 백엔드 서버를 시작하는 중...")
    backend_dir = Path(__file__).parent / "backend"
    
    # 백엔드 의존성 설치 (이미 설치된 경우 스킵)
    print("[설치] 백엔드 의존성을 확인하는 중...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "fastapi", "uvicorn", "pydantic", "python-multipart"
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass  # 이미 설치된 경우
    
    # 백엔드 서버 실행
    os.chdir(backend_dir)
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ])
    
    return backend_process

def check_npm():
    """npm 설치 확인 - 개선된 버전"""
    print("[디버그] npm 감지를 시작합니다...")
    
    # 환경변수 정보 출력
    path_env = os.environ.get('PATH', '')
    print(f"[디버그] PATH 환경변수 길이: {len(path_env)} 문자")
    
    # npm 위치 찾기
    try:
        result = subprocess.run(["where", "npm"], capture_output=True, text=True, shell=True, timeout=10)
        if result.returncode == 0:
            print(f"[디버그] npm 발견 위치:\n{result.stdout.strip()}")
        else:
            print(f"[디버그] 'where npm' 실패: {result.stderr.strip()}")
    except Exception as e:
        print(f"[디버그] npm 위치 검색 실패: {e}")
    
    # 여러 npm 경로 시도
    npm_commands = [
        "npm",
        "npm.cmd",
        r"C:\Program Files\nodejs\npm.cmd",
        os.path.expanduser(r"~\AppData\Roaming\npm\npm.cmd"),
        r"C:\Users\Administrator\AppData\Roaming\npm\npm.cmd"
    ]
    
    print(f"[디버그] {len(npm_commands)}개의 npm 경로를 시도합니다...")
    
    for i, npm_cmd in enumerate(npm_commands, 1):
        try:
            print(f"[디버그] 시도 {i}: {npm_cmd}")
            result = subprocess.run(
                [npm_cmd, "--version"], 
                check=True, 
                capture_output=True, 
                shell=True,
                timeout=10,
                env=os.environ.copy()
            )
            version = result.stdout.decode('utf-8').strip()
            print(f"[성공] npm 발견! 버전: {version}, 경로: {npm_cmd}")
            return npm_cmd
        except subprocess.TimeoutExpired:
            print(f"[실패] 시도 {i}: 타임아웃")
        except subprocess.CalledProcessError as e:
            print(f"[실패] 시도 {i}: 실행 오류 (코드 {e.returncode})")
        except FileNotFoundError:
            print(f"[실패] 시도 {i}: 파일을 찾을 수 없음")
        except Exception as e:
            print(f"[실패] 시도 {i}: {type(e).__name__}: {e}")
    
    print("[결과] 모든 npm 경로 시도가 실패했습니다.")
    return None

def run_frontend():
    """프론트엔드 서버 실행 - 개선된 버전"""
    print("[확인] npm 설치 상태를 확인하는 중...")
    
    npm_cmd = check_npm()
    if not npm_cmd:
        print("\n" + "="*50)
        print("[알림] npm을 찾을 수 없습니다!")
        print("[알림] 백엔드 전용 모드로 실행됩니다.")
        print("[정보] 웹 인터페이스: http://localhost:8000")
        print("\n[해결방법] 프론트엔드를 수동으로 실행하려면:")
        print("  1. 새 터미널을 열어서")
        print("  2. cd frontend")
        print("  3. npm run dev")
        print("="*50)
        return None
    
    print(f"[성공] npm 발견: {npm_cmd}")
    print("[시작] 프론트엔드를 시작하는 중...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print("[알림] frontend 폴더가 없습니다. 백엔드 전용 모드로 실행됩니다.")
        return None
    
    if not (frontend_dir / "node_modules").exists():
        print("[설치] 프론트엔드 의존성을 설치하는 중...")
        original_dir = os.getcwd()
        try:
            os.chdir(frontend_dir)
            result = subprocess.run([npm_cmd, "install"], 
                                  check=True, 
                                  shell=True, 
                                  env=os.environ.copy(),
                                  timeout=300)  # 5분 타임아웃
            print("[완료] 의존성 설치가 완료되었습니다.")
        except subprocess.TimeoutExpired:
            print("[오류] npm install 타임아웃 (5분 초과)")
            return None
        except subprocess.CalledProcessError as e:
            print(f"[오류] npm install 실패: 코드 {e.returncode}")
            return None
        finally:
            os.chdir(original_dir)
    
    # 프론트엔드 개발 서버 실행
    print("[실행] React 개발 서버를 시작합니다...")
    original_dir = os.getcwd()
    try:
        os.chdir(frontend_dir)
        frontend_process = subprocess.Popen(
            [npm_cmd, "run", "dev"], 
            shell=True,
            env=os.environ.copy()
        )
        return frontend_process
    except Exception as e:
        print(f"[오류] 프론트엔드 서버 실행 실패: {e}")
        return None
    finally:
        os.chdir(original_dir)

def kill_port_processes():
    """포트 3000과 8000을 사용하는 프로세스 종료 (Windows)"""
    ports_to_kill = [3000, 8000]
    for port in ports_to_kill:
        try:
            # Windows에서 netstat과 taskkill 사용
            result = subprocess.run(
                f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :{port}\') do taskkill /f /pid %a',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"[정리] 포트 {port}를 사용하는 프로세스를 종료했습니다.")
            else:
                print(f"[알림] 포트 {port}를 사용하는 프로세스가 없습니다.")
        except Exception as e:
            print(f"[알림] 포트 {port} 정리 중 오류: {e}")
            # 오류가 있어도 계속 진행
            pass

def main():
    """메인 실행 함수"""
    print("="*60)
    print("네이버 블로그 스크래퍼 웹 애플리케이션")
    print("="*60)
    
    # 포트 충돌 방지를 위한 기존 프로세스 정리
    print("[정리] 기존 프로세스를 정리하고 있습니다...")
    try:
        kill_port_processes()
        time.sleep(2)  # 프로세스 종료 대기
    except Exception as e:
        print(f"[알림] 프로세스 정리 중 오류: {e}")
    
    try:
        # 백엔드 실행
        backend_process = run_backend()
        print("[완료] 백엔드 서버가 http://localhost:8000 에서 실행 중")
        
        # 잠시 대기
        time.sleep(3)
        
        # 프론트엔드 실행 (선택적)
        frontend_process = run_frontend()
        
        if frontend_process:
            print("[완료] 프론트엔드가 http://localhost:3000 에서 실행 중")
            web_url = "http://localhost:3000"
        else:
            web_url = "http://localhost:8000"
        
        # 브라우저 열기
        time.sleep(5)
        print("[열기] 브라우저를 열고 있습니다...")
        webbrowser.open(web_url)
        
        print("\n" + "="*60)
        print("[성공] 애플리케이션이 성공적으로 시작되었습니다!")
        if frontend_process:
            print("Frontend: http://localhost:3000")
        print("웹 인터페이스: http://localhost:8000")
        print("API 문서: http://localhost:8000/docs")
        print("API Redoc: http://localhost:8000/redoc")
        print("\n종료하려면 Ctrl+C를 누르세요.")
        print("="*60)
        
        # 프로세스들이 종료될 때까지 대기
        try:
            if frontend_process:
                # 두 프로세스 모두 대기
                while backend_process.poll() is None or frontend_process.poll() is None:
                    time.sleep(1)
            else:
                # 백엔드만 대기
                backend_process.wait()
                
        except KeyboardInterrupt:
            print("\n[종료] 애플리케이션을 종료하는 중...")
            backend_process.terminate()
            if frontend_process:
                frontend_process.terminate()
            
            # 강제 종료가 필요한 경우
            time.sleep(2)
            try:
                backend_process.kill()
                if frontend_process:
                    frontend_process.kill()
            except:
                pass
            
            print("[완료] 애플리케이션이 종료되었습니다.")
    
    except subprocess.CalledProcessError as e:
        print(f"[오류] 프로세스 실행 중 오류가 발생했습니다: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"[오류] 예기치 않은 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()