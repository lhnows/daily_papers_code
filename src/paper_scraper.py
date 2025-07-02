# run.py
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import json
from src.sqlitedb import PaperDatabase
from papercode import DATA_DIR,scrape_page
from get_llm_response import get_llm_response

db = PaperDatabase()
PAPERS_DIR = "ppwcode"
os.makedirs(PAPERS_DIR, exist_ok=True)


def load_yesterday_titles():
    path = os.path.join(DATA_DIR, "yesterday_titles.txt")
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_today_titles(titles):
    path = os.path.join(DATA_DIR, "yesterday_titles.txt")
    with open(path, "w", encoding="utf-8") as f:
        for title in titles:
            f.write(title + "\n")

def save_markdown(papers):
    today = datetime.now().strftime("%Y-%m-%d")
    md_path = os.path.join(PAPERS_DIR, f"papers_{today}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Papers with Code - {today}\n\n")
  
        
        for title, link, code_links, abstract,abstract_cn, authors in papers:
            f.write(f"## 论文标题 {title}\n\n")
            f.write(f"- **中文摘要：** {abstract_cn}\n\n")
            f.write(f"- **英文摘要：** {abstract}\n\n")
            f.write(f"- **论文链接** {link}\n\n")
            f.write(f"- **代码链接** {', '.join(code_links)}\n\n")

def generate_readme():
    today = datetime.now().strftime("%Y-%m-%d")
    md_files = sorted([f for f in os.listdir(PAPERS_DIR) if f.endswith(".md")])
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 每日最新论文更新\n\n")
        f.write("本项目每天自动更新 最新论文和配套代码，并生成 Markdown 文件。\n\n")
        f.write(f"**最新更新：{today}**\n\n")
        f.write("## 每日更新列表\n")
        for name in reversed(md_files):
            f.write(f"- [{name}](ppwcode/{name})\n")


def send_to_wps_single(title, link, github_links, abstract, authors):
    # Load API URL from GitHub Actions secrets
    api_url = os.getenv('API_ENDPOINT')  # Must set this secret in GitHub
    if not api_url:
        raise ValueError("API_ENDPOINT environment variable not set!")
    headers = {
        "Content-Type": "application/json"
    }
    try:
        paper = (title, link, github_links, abstract, authors)
        paper_data = {
            "title": paper[0],
            "pdfurl": paper[1],
            "githuburl": paper[2][0],
            "abstract": paper[3], 
            "authors": paper[4]
        }

        response = requests.post(
            api_url,
            data=json.dumps(paper_data),
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"成功发送论文到WPS: {paper_data['title']}")
        else:
            print(f"发送WPS失败: {paper_data['title']}, 状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
        # 避免频繁请求，可以添加延迟
        import time
        time.sleep(1)  # 1秒间隔
        
    except Exception as e:
        print(f"发送论文到WPS时出错 {paper_data['title']}: {str(e)}")

def send_to_wps(papers):
    # API端点
    # api_url = ""
    # Load API URL from GitHub Actions secrets
    api_url = os.getenv('API_ENDPOINT')  # Must set this secret in GitHub
    if not api_url:
        raise ValueError("API_ENDPOINT environment variable not set!")
    headers = {
        "Content-Type": "application/json"
    }
    for paper in papers:
        try:

            paper_data = {
                "title": paper[0],
                "pdfurl": paper[1],
                "githuburl": paper[2][0],
                "abstract": paper[3], 
                "authors": paper[4]
            }

            response = requests.post(
                api_url,
                data=json.dumps(paper_data),
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"成功发送论文: {paper_data['title']}")
            else:
                print(f"发送失败: {paper_data['title']}, 状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                
            # 避免频繁请求，可以添加延迟
            import time
            time.sleep(1)  # 1秒间隔
            
        except Exception as e:
            print(f"发送论文时出错 {paper_data['title']}: {str(e)}")

def add_paper_to_db(title, link, github_links, abstract,abstract_cn, authors):
    paper_data = {
        'title': title,
        'pdfurl': link,
        'codeurl': github_links,
        'abstract': abstract,
        'abstract_cn': abstract_cn,
        'authors': authors,
    }
    db.insert_paper(paper_data)

def main():
    yesterday = load_yesterday_titles()
    today_titles = set()
    today_papers = []
    page = 1
    BAILIAN_GPT_KEY = os.getenv('BAILIAN_GPT_KEY')  # Must set this secret in GitHub
    if not BAILIAN_GPT_KEY:
        raise ValueError("BAILIAN_GPT_KEY environment variable not set!")
    while True:
        print(f"Fetching page {page}...")
        papers = scrape_page(page,[])
        if not papers:
            break

        stop = False
        for title, pdfurl, codeurl, abstract, authors in papers:
            if title in yesterday:
                stop = True
                break
            if title not in today_titles:
                prompt = f"请根据以下摘要，生成中文总结,不需要标题，不得出现摘要、总结字样，请直接生成总结后的内容：title:{title} abstract:{abstract}"
                abstract_cn = get_llm_response(
                                                prompt=prompt,
                                                model_name="qwen-max",
                                                api_key=BAILIAN_GPT_KEY
                                            )
                print(f"{title}\n {abstract_cn}\n")
                add_paper_to_db(title, pdfurl, codeurl, abstract, abstract_cn,authors)
                # send_to_wps_single(title, pdfurl, codeurl, abstract, abstract_cn,authors)
                today_papers.append((title, pdfurl, codeurl, abstract, abstract_cn,authors))
                today_titles.add(title)

        if stop or page >= 5:
            break
        page += 1
        # send_to_wps(papers)

    if today_papers:
        save_markdown(today_papers)
        save_today_titles(today_titles)
        generate_readme()
        print(f"Saved {len(today_papers)} new papers.")
    else:
        print("No new papers found.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
 
