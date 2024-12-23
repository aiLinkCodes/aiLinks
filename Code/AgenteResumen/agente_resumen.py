import json
import openai
import os
import sys

# Configurar clave de API de OpenAI
client = openai.Client(api_key='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')

# Función para generar un resumen usando OpenAI
def generate_summary(data):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente que resume contenido web."},
                {"role": "user", "content": f"Resume el siguiente contenido JSON y proporciona también el nombre de la empresa que aparece en los datos. Devuelve el resultado en el siguiente formato:\nResumen: <resumen>\nEmpresa: <nombre_empresa>\n\nContenido JSON: {json.dumps(data, ensure_ascii=False)}"}
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error al generar el resumen: {e}"

# Función para guardar el resumen en un archivo
def save_summary_to_file(summary, company_name):
    # Ruta relativa correcta para guardar en ../../output
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f'informacion_{company_name}.txt')
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(summary)
    print(f"Resumen guardado en {file_path}")

# Función principal
def main(data):
    # Generar resumen usando todo el JSON
    response = generate_summary(data)
    print('veamos => '+response)
    # Extraer el resumen y el nombre de la empresa de la respuesta
    summary = ""
    company_name = "empresa_desconocida"
    
    for line in response.split('\n'):
        if line.startswith('Resumen:'):
            summary = line.replace('Resumen:', '').strip()
        if line.startswith('Empresa:'):
            company_name = line.replace('Empresa:', '').strip()
    
    # Guardar resumen en archivo
    save_summary_to_file(summary, company_name)
    
    return summary

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python agente_resumen.py '<json_string>'")
        sys.exit(1)
    
    try:
        input_json = json.loads(sys.argv[1])
        result = main(input_json)
        print("Resumen devuelto como variable:")
        print(result)
    except json.JSONDecodeError:
        print("Error: El parámetro proporcionado no es un JSON válido.")
        sys.exit(1)
