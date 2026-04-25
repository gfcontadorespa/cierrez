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

    def process_cierre(self, image_urls, expected_visa_mc=None, expected_clave=None):
        """
        Envía una o varias imágenes a OpenAI para extraer datos del Cierre Z.
        :param image_urls: List of direct public URLs to the images (e.g. from Cloudflare R2).
        """
        if isinstance(image_urls, str):
            image_urls = [image_urls]

        context_prompt = ""
        if expected_visa_mc is not None or expected_clave is not None:
            context_prompt = f"""
Información de contexto proporcionada por el usuario (montos digitados manualmente):
- Total esperado VISA/MASTERCARD: {expected_visa_mc if expected_visa_mc is not None else 'No reportado'}
- Total esperado CLAVE: {expected_clave if expected_clave is not None else 'No reportado'}

INSTRUCCIÓN DE TOLERANCIA OCR:
La impresión térmica a menudo causa que la cámara confunda los números 5 y 6, 3 y 8, o 1 y 7. 
Si el texto detectado difiere del monto esperado SOLO por uno de estos errores comunes de lectura óptica, asume que el ticket en la foto dice el monto esperado y devuélvelo como el valor final.
"""

        content_blocks = [
            {"type": "text", "text": f"""
Analiza estas imágenes de comprobantes de pago (POS) y extrae los datos en formato JSON puro.
Recibirás una imagen para 'CLAVE' y otra para 'VISA/MASTERCARD' (o ambas en un solo cierre).
{context_prompt}
Campos requeridos:
1. pos_clave (Número: Busca el 'TOTAL' debajo de 'TOTALES GENERALES' en el ticket que mencione 'CLAVE'. Si no hay ticket de Clave, pon 0. ej: 26.75)
2. pos_visa_mc (Número: Debes buscar el 'TOTAL' final debajo de 'TOTALES GENERALES' de toda la tira que consolida VISA y MASTERCARD. NO te detengas en los subtotales individuales por marca de tarjeta. Usa siempre el Gran Total del cierre. ej: 108.13)

Validaciones críticas:
- La tira DEBE decir 'CIERRE' o 'SETTLEMENT ACCEPTED'.
- Responde con un ÚNICO objeto JSON plano. ej: {{"pos_clave": 10.0, "pos_visa_mc": 20.0, "debug_info": "..."}}

Responde ÚNICAMENTE con el objeto JSON puro. No incluyas ```json ni texto adicional.
"""}
        ]

        for url in image_urls:
            if url and url.startswith("http"):
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": url},
                })
            elif url and os.path.exists(url):
                # Fallback for local testing
                base64_image = self._encode_image(url)
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
