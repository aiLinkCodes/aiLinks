import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
import os
from transformers import pipeline

def validate_url(url):
    if not url.startswith(('http://', 'https://')):
        print("Agregando 'https://' al inicio de la URL...")
        url = 'https://' + url
    return url

def extract_contact_info(soup):
    text = soup.get_text(separator=" ")

    # Buscar correos electrónicos
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)

    # Buscar números de teléfono
    phones = re.findall(r'\b(?:\+?\d{1,3})?[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,9}\b', text)

    # Buscar nombres potenciales (basado en patrones simples como "Nombre Apellido")
    names = re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', text)

    return {
        "emails": list(set(emails)),  # Eliminar duplicados
        "phones": list(set(phones)),
        "names": list(set(names))
    }

def scrape_website(url):
    try:
        # Validar la URL
        url = validate_url(url)

        # Solicitud a la URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer datos
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

        # Meta descripción
        meta_description = soup.find('meta', attrs={'name': 'description'})
        data['meta_description'] = meta_description['content'] if meta_description and 'content' in meta_description.attrs else "No Meta Description"

        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        data['meta_keywords'] = meta_keywords['content'] if meta_keywords and 'content' in meta_keywords.attrs else "No Meta Keywords"

        # Headings
        for tag in ["h1", "h2", "h3"]:
            data["headings"][tag] = [heading.get_text(strip=True) for heading in soup.find_all(tag)]

        # Párrafos (Filtrando textos muy cortos)
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        data['paragraphs'] = [p for p in paragraphs if len(p) > 50]

        # Listas
        data['lists'] = [li.get_text(strip=True) for li in soup.find_all("li")]

        # Enlaces
        data['links'] = list(set([urljoin(url, a['href']) for a in soup.find_all('a', href=True)]))

        # Imágenes (con alt text)
        for img in soup.find_all('img'):
            if 'src' in img.attrs:
                img_url = urljoin(url, img['src'])
                alt_text = img.get('alt', "No Alt Text")
                if alt_text.lower() not in ["no alt text", "", "image", "photo"]:  # Filtrar alt irrelevantes
                    data['images'].append({"url": img_url, "alt": alt_text})

        # Tablas
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for row in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                rows.append(cells)
            tables.append(rows)
        data['tables'] = tables

        # Extraer información de contacto
        data['contact_info'] = extract_contact_info(soup)

        return data

    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL {url}: {e}")
        return None

def scrape_contact_pages(base_url, links, main_data):
    contact_pages = []

    # Filtrar enlaces relevantes utilizando expresiones regulares
    contact_pattern = re.compile(r'(contact|about|contacto|support|help)', re.IGNORECASE)
    for link in links:
        if contact_pattern.search(link):
            contact_pages.append(link)

    # Scrape cada página de contacto
    for page_url in contact_pages:
        print(f"Analizando página de contacto: {page_url}")
        result = scrape_website(page_url)
        if result:
            # Combinar la información de contacto con la principal
            for key, values in result['contact_info'].items():
                if key in main_data['contact_info']:
                    main_data['contact_info'][key].extend(values)
                    main_data['contact_info'][key] = list(set(main_data['contact_info'][key]))  # Eliminar duplicados

    return main_data

def generate_filename(url):
    parsed_url = urlparse(url)
    base_name = parsed_url.netloc.split('.')[-2]  # Obtener la parte del nombre de la empresa
    filename = f"{base_name}.json"
    counter = 1

    # Verificar si el archivo ya existe y generar un índice si es necesario
    while os.path.exists(filename):
        filename = f"{base_name}{counter}.json"
        counter += 1

    return filename

def deduplicate_json(data):
    # Eliminar enlaces duplicados
    data['links'] = list(set(data['links']))
    return data

def generate_summary(json_data):
    summarizer = pipeline("summarization")

    # Preparar datos clave para el resumen
    title = json_data.get("title", "No Title")
    description = json_data.get("meta_description", "No Description Available")
    paragraphs = " ".join(json_data.get("paragraphs", [])[:3])  # Limitar a los primeros 3 párrafos

    # Resumir contenido principal
    input_text = f"Title: {title}\nDescription: {description}\nContent: {paragraphs}"
    summary = summarizer(input_text, max_length=130, min_length=30, do_sample=False)

    return summary[0]['summary_text']

# Ejemplo de uso
if __name__ == "__main__":
    url = 'https://www.salicru.com'
    result = scrape_website(url)
    if result:
        # Analizar páginas de contacto y combinar la información
        result = scrape_contact_pages(url, result['links'], result)

        # Depurar datos para eliminar duplicados
        result = deduplicate_json(result)

        # Generar nombre del archivo basado en la empresa
        output_file = generate_filename(url)

        # Guardar el resultado combinado como JSON
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=4)
        print(f"Datos combinados extraídos y guardados en '{output_file}'")

        # Generar resumen utilizando modelo de lenguaje natural
        summary = generate_summary(result)
        print("Resumen Generado:")
        print(summary)

        # Guardar el resumen como un archivo .txt
        summary_file = output_file.replace(".json", ".txt")
        with open(summary_file, "w", encoding="utf-8") as file:
            file.write(summary)
        print(f"Resumen guardado en '{summary_file}'")
