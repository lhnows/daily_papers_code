# run.py
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import json

DATA_DIR = "data"
PAPERS_DIR = "ppwcode"
BASE_URL = "https://paperswithcode.com/latest?page={}"
PWC_BASE = "https://paperswithcode.com"

os.makedirs(DATA_DIR, exist_ok=True)
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

def resolve_github_links_and_pdf(code_url):
    github_links = set()
    paper_pdf_link = ""
    try:
        full_url = PWC_BASE + code_url
        res = requests.get(full_url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup.select("a.code-table-link"):
            href = tag.get("href", "")
            if 'github.com' in href:
                github_links.add(href.strip())

        for a_tag in soup.select("a"):
            href = a_tag.get("href", "")
            if href.endswith(".pdf") and not href.startswith(PWC_BASE):
                paper_pdf_link = href
                break
    except Exception:
        pass
    return list(github_links), paper_pdf_link

def scrape_paper_details(paper_url):
    abstract = ""
    authors = []
    try:
        res = requests.get(paper_url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        abs_tag = soup.select_one(".paper-abstract p")
        if abs_tag:
            abstract = abs_tag.text.strip()
        authors = [a.text.strip() for a in soup.select("span.author-name")]
    except Exception:
        pass
    return abstract, ", ".join(authors)

def scrape_page(page_num):
    url = BASE_URL.format(page_num)
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    papers = []
    for item in soup.select("div.item.paper-card"):
        title_tag = item.select_one("h1 a")
        if not title_tag:
            continue
        title = title_tag.text.strip()
        pwc_link = PWC_BASE + title_tag["href"]

        abstract, authors = scrape_paper_details(pwc_link)

        code_tag = item.select_one("a.badge")
        raw_code_link = code_tag["href"] if code_tag else ""
        github_links, paper_pdf_link = resolve_github_links_and_pdf(raw_code_link) if raw_code_link else ([], "")

        link = paper_pdf_link if paper_pdf_link else pwc_link
        papers.append((title, link, github_links, abstract, authors))
        send_to_wps_single(title, link, github_links, abstract, authors)
        send_to_coze_single(title, link, github_links, abstract, authors)
    return papers

def save_markdown(papers):
    today = datetime.now().strftime("%Y-%m-%d")
    md_path = os.path.join(PAPERS_DIR, f"papers_{today}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Papers with Code - {today}\n\n")
        f.write("| 论文 | 代码 | 摘要 | 作者 |\n")
        f.write("|------|------|------|------|\n")
        for title, link, code_links, abstract, authors in papers:
            unique_links = sorted(set(code_links))
            title_md = f"[{title}]({link})"
            codes_md = ", ".join(f"[GitHub]({url})" for url in unique_links) if unique_links else ""
            abstract_md = abstract.replace("|", " ").replace("\n", " ").strip()
            authors_md = authors.replace("|", " ").strip()
            f.write(f"| {title_md} | {codes_md} | {abstract_md} | {authors_md} |\n")

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

def send_to_coze_single(title, link, github_links, abstract, authors):
    api_url = os.getenv('COZEWEBHOOK')  # Must set this secret in GitHub
    if not api_url:
        raise ValueError("COZEWEBHOOK environment variable not set!")
    headers = {
        "Authorization": os.getenv('COZEAUTHORIZATION'),
        "Content-Type": "application/json"
    }
    try:
        paper = (title, link, github_links, abstract, authors)
        paper_data = {
            "title": paper[0],
            "pdfurl": paper[1],
            "codeurl": paper[2][0],
            "abstract": paper[3], 
            "authors": paper[4]
        }

        response = requests.post(
            api_url,
            data=json.dumps(paper_data),
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"成功发送论文到COZE: {paper_data['title']}")
        else:
            print(f"发送COZE失败: {paper_data['title']}, 状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
        # 避免频繁请求，可以添加延迟
        import time
        time.sleep(1)  # 1秒间隔
        
    except Exception as e:
        print(f"发送论文到COZE时出错 {paper_data['title']}: {str(e)}")

def coze_gen_abstractcn_paperclass():
    api_url = os.getenv('COZE_ABSTRACTCN_PAPERCLASS_WEBHOOK')  # Must set this secret in GitHub
    if not api_url:
        raise ValueError("COZE_ABSTRACTCN_PAPERCLASS_WEBHOOK environment variable not set!")
    headers = {
        "Authorization": os.getenv('COZE_ABSTRACTCN_PAPERCLASS_WEBHOOK_AUTHORIZATION'),
        "Content-Type": "application/json"
    }
    try:
        paper_data = {
        }
        response = requests.post(
            api_url,
            data=json.dumps(paper_data),
            headers=headers
        )
        if response.status_code == 200:
            print(f"调用成功")
        else:
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"调用COZE生成中文摘要与分类出错 : {str(e)}")

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

def main():
    yesterday = load_yesterday_titles()
    today_titles = set()
    today_papers = []
    page = 1

    while True:
        print(f"Fetching page {page}...")
        papers = scrape_page(page)
        if not papers:
            break

        stop = False
        for title, *rest in papers:
            if title in yesterday:
                stop = True
                break
            if title not in today_titles:
                today_papers.append((title, *rest))
                today_titles.add(title)

        if stop or page >= 10:
            break
        page += 1
        # send_to_wps(papers)

    if today_papers:
        coze_gen_abstractcn_paperclass()
        save_markdown(today_papers)
        save_today_titles(today_titles)
        generate_readme()
        print(f"Saved {len(today_papers)} new papers.")
    else:
        print("No new papers found.")

if __name__ == "__main__":
    main()
