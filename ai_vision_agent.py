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

    def process_cierre(self, image_paths, expected_visa_mc=None, expected_clave=None):
        """
        Envía una o varias imágenes a OpenAI para extraer datos del Cierre Z.
        :param image_paths: List of absolute paths to images.
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]

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

    def process_deposito(self, image_path, expected_monto=None):
        """
        Analiza una imagen de un volante de depósito bancario.
        """
        if not os.path.exists(image_path):
            return {"error": "Archivo no encontrado"}

        context_prompt = ""
        if expected_monto is not None:
            context_prompt = f"""
Información de contexto proporcionada por el usuario:
- Monto del depósito esperado: {expected_monto}

INSTRUCCIÓN DE TOLERANCIA OCR:
A veces el sello del banco o la impresión cortada hacen que la IA confunda 5 y 6, 3 y 8, o 1 y 7, o no pueda leer bien los centavos.
Si el texto en la foto difiere del valor esperado SOLO por este tipo de errores de lectura óptica, asume que el volante corresponde al valor esperado y devuélvelo como resultante.
"""

        base64_image = self._encode_image(image_path)
        content_blocks = [
            {"type": "text", "text": f"""
Analiza esta imagen de un volante de depósito bancario legítimo y extrae los datos en formato JSON puro. Solo hay UNA foto por depósito.
{context_prompt}
Campos requeridos:
1. monto (Número: Busca el 'TOTAL PROCESADO' o 'EFECTIVO' impreso por la máquina, o el 'TOTAL US$' escrito a mano. ej: 130.58)
2. fecha (Texto: Busca la fecha de depósito impresa. Formato YYYY-MM-DD. ej: '2026-01-16')

Validaciones críticas:
- Debe ser un volante de depósito bancario legítimo.
- Prioriza siempre el monto impreso por la terminal bancaria o el que tenga el sello.
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
