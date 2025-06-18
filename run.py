# run.py
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

DATA_DIR = "data"
PAPERS_DIR = "papers"
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
    github_links = []
    paper_pdf_link = ""
    try:
        full_url = PWC_BASE + code_url
        res = requests.get(full_url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup.select("a.code-table-link"):
            href = tag.get("href", "")
            if 'github.com' in href:
                github_links.append(href)

        for a_tag in soup.select("a"):
            href = a_tag.get("href", "")
            if href.endswith(".pdf") and not href.startswith(PWC_BASE):
                paper_pdf_link = href
                break
    except Exception:
        pass
    return github_links, paper_pdf_link

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
    return papers

def save_markdown(papers):
    today = datetime.now().strftime("%Y-%m-%d")
    md_path = os.path.join(PAPERS_DIR, f"papers_{today}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Papers with Code - {today}\n\n")
        f.write("| 论文 | 代码 | 摘要 | 作者 |\n")
        f.write("|------|------|------|------|\n")
        for title, link, code_links, abstract, authors in papers:
            title_md = f"[{title}]({link})"
            codes_md = ", ".join(f"[GitHub]({url})" for url in code_links) if code_links else ""
            abstract_md = abstract.replace("|", " ").replace("\n", " ").strip()
            authors_md = authors.replace("|", " ").strip()
            f.write(f"| {title_md} | {codes_md} | {abstract_md} | {authors_md} |\n")

def generate_readme():
    today = datetime.now().strftime("%Y-%m-%d")
    md_files = sorted([f for f in os.listdir(PAPERS_DIR) if f.endswith(".md")])
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 每日最新论文更新\n\n")
        f.write("本项目每天自动从 [PapersWithCode](https://paperswithcode.com/latest) 获取最新论文、代码和真实论文 PDF 链接，并生成 Markdown 文件。\n\n")
        f.write(f"**最新更新：{today}**\n\n")
        f.write("## 每日更新列表\n")
        for name in reversed(md_files):
            f.write(f"- [{name}](papers/{name})\n")

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

    if today_papers:
        save_markdown(today_papers)
        save_today_titles(today_titles)
        generate_readme()
        print(f"Saved {len(today_papers)} new papers.")
    else:
        print("No new papers found.")

if __name__ == "__main__":
    main()