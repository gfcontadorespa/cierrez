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

    def process_cierre(self, image_path):
        """
        Envía la imagen a OpenAI para extraer datos del Cierre Z.
        """
        base64_image = self._encode_image(image_path)
        
        prompt = """
        Analiza esta imagen de un Cierre Z (comprobante de caja) y extrae los siguientes datos en formato JSON puro. 
        Si no encuentras un dato, pon 0 o null según corresponda.
        
        Campos requeridos:
        1. num_cierre (número entero)
        2. ventas_gravables (número)
        3. ventas_exentas (número)
        4. impuesto (número)
        5. total_ingresos (número total de ventas del día)
        6. efectivo (monto en efectivo)
        7. yappy (monto pagado por Yappy)
        8. pos_clave (monto pagado con tarjeta Clave)
        9. pos_visa_mc (monto pagado con Visa/Mastercard)
        10. total_pagos (suma de todos los métodos de pago)
        
        Responde ÚNICAMENTE con el objeto JSON, sin bloques de código ```json ni texto adicional.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )
            
            content = response.choices[0].message.content.strip()
            # Clean possible markdown code blocks if the model ignored instructions
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"Error procesando imagen con AI Vision: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test simple (necesita una imagen real para funcionar)
    agent = AIVisionAgent()
    # print(agent.process_cierre("test_image.jpg"))
