import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
import os

# Validar URL
def validate_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

# Extraer información de contacto
def extract_contact_info(soup):
    text = soup.get_text(separator=" ")
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phones = re.findall(r'\b(?:\+?\d{1,3})?[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,9}\b', text)
    names = re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', text)
    return {
        "emails": list(set(emails)),
        "phones": list(set(phones)),
        "names": list(set(names))
    }

# Scraper principal
def scrape_website(url):
    try:
        url = validate_url(url)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        data = {
            "url": url,
            "title": soup.title.string if soup.title else "No Title",
            "meta_description": "",
            "meta_keywords": "",
            "headings": {"h1": [], "h2": [], "h3": []},
            "paragraphs": [],
            "lists": [],
            "links": [],
            "images": [],
            "tables": [],
            "contact_info": {}
        }

        meta_description = soup.find('meta', attrs={'name': 'description'})
        data['meta_description'] = meta_description['content'] if meta_description and 'content' in meta_description.attrs else "No Meta Description"
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        data['meta_keywords'] = meta_keywords['content'] if meta_keywords and 'content' in meta_keywords.attrs else "No Meta Keywords"

        for tag in ["h1", "h2", "h3"]:
            data["headings"][tag] = [heading.get_text(strip=True) for heading in soup.find_all(tag)]

        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        data['paragraphs'] = [p for p in paragraphs if len(p) > 50]
        data['lists'] = [li.get_text(strip=True) for li in soup.find_all("li")]
        data['links'] = list(set([urljoin(url, a['href']) for a in soup.find_all('a', href=True)]))

        for img in soup.find_all('img'):
            if 'src' in img.attrs:
                img_url = urljoin(url, img['src'])
                alt_text = img.get('alt', "No Alt Text")
                if alt_text.lower() not in ["no alt text", "", "image", "photo"]:
                    data['images'].append({"url": img_url, "alt": alt_text})

        tables = []
        for table in soup.find_all('table'):
            rows = []
            for row in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                rows.append(cells)
            tables.append(rows)
        data['tables'] = tables

        data['contact_info'] = extract_contact_info(soup)
        return data

    except requests.exceptions.RequestException:
        return None

# Filtrar páginas de contacto
def scrape_contact_pages(base_url, links, main_data):
    contact_pages = []
    contact_pattern = re.compile(r'(contact|about|contacto|support|help)', re.IGNORECASE)
    for link in links:
        if contact_pattern.search(link):
            contact_pages.append(link)

    for page_url in contact_pages:
        result = scrape_website(page_url)
        if result:
            for key, values in result['contact_info'].items():
                if key in main_data['contact_info']:
                    main_data['contact_info'][key].extend(values)
                    main_data['contact_info'][key] = list(set(main_data['contact_info'][key]))
    return main_data

# Generar nombre del archivo
def generate_filename(url):
    parsed_url = urlparse(url)
    base_name = parsed_url.netloc.split('.')[-2]
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../output'))
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{base_name}.json")
    counter = 1
    while os.path.exists(filename):
        filename = os.path.join(output_dir, f"{base_name}{counter}.json")
        counter += 1
    return filename

# Eliminar duplicados
def deduplicate_json(data):
    data['links'] = list(set(data['links']))
    return data

# Scraper como función reutilizable
def run_scraper(url):
    result = scrape_website(url)
    if result:
        result = scrape_contact_pages(url, result['links'], result)
        result = deduplicate_json(result)
        output_file = generate_filename(url)
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=4)
        return result

# Ejemplo de uso
if __name__ == "__main__":
    url = 'https://www.salicru.com'
    result = run_scraper(url)
