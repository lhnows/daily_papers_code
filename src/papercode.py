import os
import requests
from bs4 import BeautifulSoup
DATA_DIR = "../data"

BASE_URL = "https://paperswithcode.com/latest?page={}"
PWC_BASE = "https://paperswithcode.com"

os.makedirs(DATA_DIR, exist_ok=True)



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

def scrape_page(page_num,func_list):
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
        print(f"发现文章:{title}")
        for func in func_list:
            func(title, link, github_links, abstract, authors)
    return papers