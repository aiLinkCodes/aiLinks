# Code/orquestador.py

from Scrapper.scrapper2 import run_scraper  # Función principal del scraper
from AgenteResumen.agente_resumen import main as process_summary  # Función principal de AgenteResumen


def main():
    """
    Orquesta el flujo del proceso: scraping → procesamiento IA → salida.
    """
    try:
        # 1. Entrada del usuario
        url = 'https://www.salicru.com'
        # url = input("Introduce el enlace para scraping: ")

        # 2. Ejecutar el scraper y obtener datos en formato JSON
        scraped_data = run_scraper(url)  # Llama a la función principal de scraping

        print("\n[INFO] Scraping completado. Datos obtenidos en formato JSON.\n")

        # 3. Procesar JSON con AgenteResumen
        summary = process_summary(scraped_data)  # Se pasa el JSON directamente
        # 4. Mostrar resultados en consola

    except Exception as e:
        print(f"[ERROR] Se produjo un error durante el flujo de trabajo: {e}")


if __name__ == "__main__":
    main()
