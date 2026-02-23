import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AIVisionAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def process_cierre(self, image_paths):
        """
        Envía una o varias imágenes a OpenAI para extraer datos del Cierre Z.
        :param image_paths: List of absolute paths to images.
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        content_blocks = [
            {"type": "text", "text": """
Analiza estas imágenes de un Cierre Z y extrae los datos en formato JSON puro.
La información puede estar en varias imágenes (Encabezado, Ventas, Pagos).

Campos requeridos:
1. num_cierre (Número entero que sigue a 'Arqueo: Z Numero:', ej: 1044)
2. fecha (Fecha del arqueo en formato YYYY-MM-DD, ej: '2025-09-20')
3. caja (Identificador de la caja - SOLO LETRAS, ej: 'AA', 'AB')
4. vendedor (Nombre del vendedor, ej: 'YISSEL REYES')
5. ventas_gravables (Número: En la tabla 'IMPUESTOS', es el monto bajo 'BASE IMP.' de la línea 'IVA 7%' o 'IVA 10%')
6. ventas_exentas (Número: En la tabla 'IMPUESTOS', es el monto bajo 'BASE IMP.' de la línea 'IVA 0%' o 'EXENTO')
7. impuesto (Número: En la tabla 'IMPUESTOS', es el monto bajo 'Cuota' de la línea 'IVA 7%' o 'IVA 10%')
8. total_ingresos (Número: ventas totales del día)
9. efectivo (Número: monto en efectivo según reporte)
10. yappy (Número: monto Yappy)
11. pos_clave (Número: monto Clave)
12. pos_visa_mc (Número: monto Visa/Mastercard)
13. total_pagos (Número: suma de todos los pagos)

Responde ÚNICAMENTE con el objeto JSON puro. No incluyas ```json ni texto adicional.
"""}
        ]

        for path in image_paths:
            if os.path.exists(path):
                base64_image = self._encode_image(path)
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content_blocks}],
                max_tokens=800,
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"Error procesando imágenes con AI Vision: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test simple (necesita una imagen real para funcionar)
    agent = AIVisionAgent()
    # print(agent.process_cierre("test_image.jpg"))
