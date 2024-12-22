import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json

def purgar_enlaces(enlaces):
    palabras_excluir = ["directorio", "ranking", "listado", "busqueda", "noticias", "expansion", "elpais", "eleconomista", "infoisinfo"]
    enlaces_filtrados = []
    for enlace in enlaces:
        if not any(palabra in enlace for palabra in palabras_excluir):
            enlaces_filtrados.append(enlace)
    return enlaces_filtrados

def obtener_dominio_base(url):
    try:
        parsed_url = urlparse(url)
        dominio = parsed_url.netloc
        return dominio.replace("www.", "")
    except Exception:
        return None

def extraer_contenido_enlace(enlace):
    try:
        print(f"Extrayendo contenido de: {enlace}")
        response = requests.get(enlace, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        
        metadata = {
            "titulo": soup.title.string if soup.title else "Sin título",
            "descripcion": soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "Sin descripción",
            "og_title": soup.find("meta", {"property": "og:title"})["content"] if soup.find("meta", {"property": "og:title"}) else "Sin título Open Graph",
            "og_description": soup.find("meta", {"property": "og:description"})["content"] if soup.find("meta", {"property": "og:description"}) else "Sin descripción Open Graph"
        }

        contenido = soup.get_text()[:500]
        dominio_base = obtener_dominio_base(enlace)

        return {
            "enlace": enlace,
            "dominio": dominio_base,
            "metadata": metadata,
            "contenido": contenido
        }
    except Exception as e:
        print(f"Error al procesar {enlace}: {e}")
        return {"enlace": enlace, "error": str(e)}

def obtener_enlaces_directorios(palabra_clave, ubicacion, num_paginas=5):
    enlaces = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for pagina in range(num_paginas):
        print(f"Scraping página {pagina + 1}...")
        url = f"https://www.google.com/search?q={palabra_clave}+en+{ubicacion}&start={pagina * 10}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error al acceder a Google: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        resultados = soup.select(".tF2Cxc")
        
        for resultado in resultados:
            enlace = resultado.select_one(".yuRUbf a")["href"] if resultado.select_one(".yuRUbf a") else None
            if enlace:
                enlaces.append(enlace)

    return purgar_enlaces(enlaces)

def main():
    palabra_clave = "empresas de maquinaria"
    ubicacion = "Barcelona"
    num_paginas = 3

    enlaces_directorios = obtener_enlaces_directorios(palabra_clave, ubicacion, num_paginas)

    contenido_empresas = []
    errores_empresas = []
    for enlace in enlaces_directorios:
        contenido = extraer_contenido_enlace(enlace)
        if "error" in contenido:
            errores_empresas.append(contenido)
        else:
            contenido_empresas.append(contenido)

    with open("empresas_purgadas_metadata.json", "w", encoding="utf-8") as f:
        json.dump(contenido_empresas, f, ensure_ascii=False, indent=4)

    with open("errores_empresas.json", "w", encoding="utf-8") as f:
        json.dump(errores_empresas, f, ensure_ascii=False, indent=4)

    print(f"Empresas escaneadas correctamente: {len(contenido_empresas)}")
    print(f"Empresas con errores: {len(errores_empresas)}")

if __name__ == "__main__":
    main()
