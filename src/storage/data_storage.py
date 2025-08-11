import json
import csv
import sqlite3
import os
from datetime import datetime
from typing import Dict, List
import pandas as pd

class DataStorage:
    """추출된 데이터 저장 관리"""
    
    def __init__(self, db_path: str = "data/blog_data.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
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
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def save_to_csv(self, data: List[Dict], filepath: str):
        """CSV 형식으로 저장"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
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
            json.dumps(data.get('images', []), ensure_ascii=False),
            json.dumps(data.get('tags', []), ensure_ascii=False),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
    def export_to_markdown(self, data: Dict, filepath: str):
        """Markdown 형식으로 export"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {data.get('title', '제목 없음')}\n\n")
            f.write(f"**작성자**: {data.get('author', '알 수 없음')}\n")
            f.write(f"**작성일**: {data.get('date', '날짜 없음')}\n\n")
            f.write("---\n\n")
            f.write(data.get('content', ''))
            
            if data.get('images'):
                f.write("\n\n## 이미지\n\n")
                for img in data['images']:
                    if isinstance(img, dict):
                        f.write(f"![{img.get('alt', '')}]({img.get('local_path', '')})\n")
                        
    def get_all_posts(self) -> List[Dict]:
        """데이터베이스에서 모든 포스트 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM blog_posts')
        columns = [description[0] for description in cursor.description]
        posts = []
        
        for row in cursor.fetchall():
            post = dict(zip(columns, row))
            # JSON 문자열을 파싱
            if post.get('images'):
                post['images'] = json.loads(post['images'])
            if post.get('tags'):
                post['tags'] = json.loads(post['tags'])
            posts.append(post)
            
        conn.close()
        return posts