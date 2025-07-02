import sqlite3
import json
from typing import List, Dict, Optional

class PaperDatabase:
    def __init__(self, db_path: str = '../data/papers.db'):
        """初始化数据库连接"""
        self.conn = sqlite3.connect(db_path)
        self.create_table()
    
    def create_table(self):
        """创建数据表"""
        sql = """
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            pdfurl TEXT,
            codeurl TEXT,
            abstract TEXT,
            abstract_cn TEXT,
            authors TEXT,
            is_reported INTEGER DEFAULT 0,
            is_deep_readed INTEGER DEFAULT 0
        )
        """
        self.conn.execute(sql)
        self.conn.commit()
    
    def insert_paper(self, paper: Dict):
        """
        插入单篇论文
        :param paper: 包含title/pdfurl/codeurl/abstract/abstract_cn/authors的字典
        """
        sql = """
        INSERT INTO papers (title, pdfurl, codeurl, abstract, abstract_cn, authors, is_reported, is_deep_readed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        # authors_json = json.dumps(paper.get('authors', []))
      
        params = (
            paper['title'],
            paper.get('pdfurl'),
            json.dumps(paper.get('codeurl', [])),
            paper.get('abstract'),
            paper.get('abstract_cn'),
            paper.get('authors'),
            0,
            0
        )
        cursor = self.conn.execute(sql, params)
        self.conn.commit()
        return cursor.lastrowid  # 返回插入的ID
    
    def batch_insert_papers(self, papers: List[Dict]):
        """批量插入多篇论文"""
        sql = """
        INSERT INTO papers (title, pdfurl, codeurl, abstract, abstract_cn, authors, is_reported, is_deep_readed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            (
                p['title'],
                p.get('pdfurl'),
                p.get('codeurl'),
                p.get('abstract'),
                p.get('abstract_cn'),
                json.dumps(p.get('authors', [])),
                0,
                0
            ) for p in papers
        ]
        self.conn.executemany(sql, params)
        self.conn.commit()
    
    def get_paper_by_id(self, paper_id: int) -> Optional[Dict]:
        """根据ID查询单篇论文"""
        sql = "SELECT * FROM papers WHERE id = ?"
        cursor = self.conn.execute(sql, (paper_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_papers_by_title(self, title: str) -> List[Dict]:
        """根据标题模糊查询论文"""
        sql = "SELECT * FROM papers WHERE title LIKE ? AND is_reported = 0"
        cursor = self.conn.execute(sql, (f'%{title}%',))
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_all_papers(self) -> List[Dict]:
        """获取所有未被报道的论文"""
        cursor = self.conn.execute("SELECT * FROM papers WHERE is_reported = 0")
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def update_paper(self, paper_id: int, update_data: Dict):
        """
        更新论文信息
        :param paper_id: 要更新的论文ID
        :param update_data: 包含要更新字段的字典
        """
        set_clauses = []
        params = []
        for field in ['title', 'pdfurl', 'codeurl', 'abstract', 'abstract_cn', 'is_reported', 'is_deep_readed']:
            if field in update_data:
                set_clauses.append(f"{field} = ?")
                params.append(update_data[field])
        
        if 'authors' in update_data:
            set_clauses.append("authors = ?")
            params.append(json.dumps(update_data['authors']))
        
        if not set_clauses:
            return False
        
        params.append(paper_id)
        sql = f"UPDATE papers SET {', '.join(set_clauses)} WHERE id = ?"
        self.conn.execute(sql, params)
        self.conn.commit()
        return True
    
    def delete_paper(self, paper_id: int) -> bool:
        """删除指定ID的论文"""
        sql = "DELETE FROM papers WHERE id = ?"
        cursor = self.conn.execute(sql, (paper_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def _row_to_dict(self, row) -> Dict:
        """将数据库行转换为字典"""
        return {
            'id': row[0],
            'title': row[1],
            'pdfurl': row[2],
            'codeurl': row[3],
            'abstract': row[4],
            'abstract_cn': row[5],
            'authors': json.loads(row[6]) if row[6] else [],
            'is_reported': bool(row[7]),
            'is_deep_readed': bool(row[8])
        }
    
    def __del__(self):
        """析构时关闭数据库连接"""
        self.conn.close()


# 使用示例
if __name__ == '__main__':
    db = PaperDatabase()
    
    # 插入示例
    paper1 = {
        "title": "深度学习在图像识别中的应用",
        "pdfurl": "http://example.com/dl_image.pdf",
        "codeurl": "http://github.com/dl-image-repo",
        "abstract": "This paper explores deep learning...",
        "abstract_cn": "本文探讨了深度学习在...",
        "authors": ["张三", "李四"]
    }
    inserted_id = db.insert_paper(paper1)
    print(f"插入论文ID: {inserted_id}")
    
    # 批量插入
    papers = [
        {
            "title": "自然语言处理进展",
            "pdfurl": "http://example.com/nlp.pdf",
            "authors": ["王五", "赵六"]
        },
        {
            "title": "计算机视觉最新技术",
            "codeurl": "http://github.com/cv-tech",
            "abstract": "Recent advances in computer vision..."
        }
    ]
    db.batch_insert_papers(papers)
    
    # 查询示例
    print("\n所有论文:")
    for paper in db.get_all_papers():
        print(f"{paper['id']}: {paper['title']}")
    
    print("\n搜索包含'深度'的论文:")
    for paper in db.get_papers_by_title("深度"):
        print(f"{paper['title']} - 作者: {', '.join(paper['authors'])}")
    
    # 更新示例
    update_data = {
        "abstract": "Updated abstract content...",
        "authors": ["张三", "李四", "王五"]
    }
    if db.update_paper(inserted_id, update_data):
        print("\n更新后的论文信息:")
        print(db.get_paper_by_id(inserted_id))
    
    # 删除示例
    if db.delete_paper(inserted_id):
        print(f"\n已删除ID为{inserted_id}的论文")