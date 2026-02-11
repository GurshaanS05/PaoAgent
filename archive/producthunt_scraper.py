import time
import re
import pandas as pd
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests

PRODUCTHUNT_URL = 'https://www.producthunt.com/'
CSV_OUTPUT = 'ai_companies.csv'
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}')
COMMON_PATHS = ['/contact', '/about', '/support', '/team', '/company']


def get_product_links():
    """Use Selenium to get product links from Product Hunt homepage."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(PRODUCTHUNT_URL)
    print("Waiting for products to load...")
    time.sleep(8)
    html = driver.page_source
    print(f"HTML length: {len(html)}")
    print("Sample HTML (first 1000 chars):\n", html[:1000])
    soup = BeautifulSoup(html, 'html.parser')
    # Find all anchor tags that link to /posts/...
    product_links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/posts/'):
            product_links.add(urljoin(PRODUCTHUNT_URL, href))
    print(f"Found {len(product_links)} product links.")
    driver.quit()
    return list(product_links)

def get_product_info(product_url):
    """Visit the Product Hunt product page and extract name, description, and external website URL."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(product_url)
    time.sleep(5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # Name
    name_tag = soup.find('h1')
    name = name_tag.text.strip() if name_tag else ''
    # Description
    desc_tag = soup.find('meta', {'name': 'description'})
    desc = desc_tag['content'].strip() if desc_tag and desc_tag.has_attr('content') else ''
    # External website
    ext_link = soup.find('a', {'data-test': 'header-visit-website'})
    website = ext_link['href'] if ext_link and ext_link.get('href') else None
    print(f"  Product: {name}")
    print(f"  Description: {desc[:100]}...")
    print(f"  Website: {website}")
    driver.quit()
    return name, desc, website

def find_emails_on_website(base_url, max_pages=6):
    checked = set()
    found_emails = set()
    to_check = [base_url]
    for path in COMMON_PATHS:
        to_check.append(urljoin(base_url, path))
    for url in to_check[:max_pages]:
        if url in checked:
            continue
        checked.add(url)
        print(f"    Crawling: {url}")
        try:
            resp = requests.get(url, timeout=10)
            emails = set(EMAIL_REGEX.findall(resp.text))
            if emails:
                print(f"    Found emails: {emails}")
                found_emails.update(emails)
        except Exception as e:
            print(f"    Error crawling {url}: {e}")
            continue
    return list(found_emails)

def main():
    print('Scraping Product Hunt homepage for product links...')
    product_links = get_product_links()
    print(f'Found {len(product_links)} product pages.')
    rows = []
    for i, prod_url in enumerate(product_links):
        print(f"Processing product {i+1}/{len(product_links)}: {prod_url}")
        name, desc, website = get_product_info(prod_url)
        if not (name and website):
            print('  Missing name or website, skipping.')
            continue
        emails = find_emails_on_website(website)
        if not emails:
            print('  No emails found, skipping.')
            continue
        email = emails[0]  # Pick the first found
        rows.append({
            'company_name': name,
            'contact_name': '',
            'email': email,
            'short_description': desc,
            'full_description': desc,
        })
        print(f'  Added: {name} <{email}>')
        time.sleep(2)
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(CSV_OUTPUT, index=False)
        print(f'Wrote {len(rows)} companies to {CSV_OUTPUT}')
    else:
        print('No companies with emails found.')

if __name__ == '__main__':
    main() 