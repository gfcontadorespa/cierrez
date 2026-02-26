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
Analiza estas imágenes de comprobantes de pago (POS) y extrae los datos en formato JSON puro.
Solo debes enfocarte en los cierres de tarjetas Visa/Mastercard y Clave.

Campos requeridos:
1. pos_clave (Número: En la imagen de Clave, busca el 'TOTAL' al final de la tira. ej: 26.75)
2. pos_visa_mc (Número: En la imagen de Visa/Mastercard, busca el 'TOTAL' al final de la tira que suma Visa y Mastercard. ej: 544.64)

Validaciones críticas:
- La tira DEBE decir 'CIERRE' o 'SETTLEMENT ACCEPTED'.
- La tira de Visa/MC DEBE mencionar 'VISA' o 'MASTERCARD'.
- La tira de Clave DEBE mencionar 'CLAVE'.

Si alguna validación falla para una imagen específica, pon ese monto en 0. Reporta el motivo exacto del fallo en un campo 'debug_info' dentro del JSON.

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

    def process_deposito(self, image_path):
        """
        Analiza una imagen de un volante de depósito bancario.
        """
        if not os.path.exists(image_path):
            return {"error": "Archivo no encontrado"}

        base64_image = self._encode_image(image_path)
        content_blocks = [
            {"type": "text", "text": """
Analiza esta imagen de un volante de depósito bancario y extrae los datos en formato JSON puro.

Campos requeridos:
1. monto (Número: El total depositado. ej: 154.50)
2. fecha (Texto: La fecha que aparece en el sello o impreso del banco. ej: '2026-02-25')

Validaciones críticas:
- Debe ser un volante de depósito (Banco General, Banistmo, etc.) o un comprobante de transferencia/Yappy.
- Si no parece un comprobante bancario legítimo, pon el monto en 0 y explica por qué en 'debug_info'.

Responde ÚNICAMENTE con el objeto JSON puro.
"""},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content_blocks}],
                max_tokens=400,
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"Error procesando depósito con AI Vision: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test simple (necesita una imagen real para funcionar)
    agent = AIVisionAgent()
    # print(agent.process_cierre("test_image.jpg"))
