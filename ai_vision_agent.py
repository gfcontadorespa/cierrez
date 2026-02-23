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
Analiza estas imágenes de un Cierre Z (comprobante de caja) y extrae los siguientes datos en formato JSON puro.
Es posible que la información esté repartida en varias imágenes (ej: una para el encabezado, otra para las ventas, otra para el datafono).

Campos requeridos:
1. num_cierre (número entero - busca en el encabezado)
2. ventas_gravables (número - monto neto con impuesto 7% o 10%)
3. ventas_exentas (número - monto sin impuestos)
4. impuesto (número - ITBMS total)
5. total_ingresos (número total de ventas del día)
6. efectivo (monto en efectivo según el reporte de caja)
7. yappy (monto pagado por Yappy)
8. pos_clave (monto pagado con tarjeta Clave / Débito local)
9. pos_visa_mc (monto pagado con Visa/Mastercard)
10. total_pagos (suma de todos los métodos de pago extraídos de las fotos)

Responde ÚNICAMENTE con el objeto JSON, sin bloques de código ```json ni texto adicional.
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
