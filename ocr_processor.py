import easyocr
import cv2
import numpy as np
import os

class OCRProcessor:
    def __init__(self, languages=['es', 'en']):
        """
        Inicializa el lector de EasyOCR.
        :param languages: Lista de idiomas a soportar (por defecto español e inglés).
        """
        print("Cargando modelos de OCR (esto puede tardar la primera vez)...")
        self.reader = easyocr.Reader(languages)

    def process_image(self, image_path):
        """
        Lee una imagen y extrae el texto.
        :param image_path: Ruta al archivo de imagen.
        :return: Lista de strings con el texto detectado.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"No se encontró la imagen: {image_path}")

        print(f"Procesando imagen: {image_path}")
        # Leemos la imagen
        results = self.reader.readtext(image_path)
        
        # results es una lista de tuplas: (bbox, text, confidence)
        extracted_text = [text for (bbox, text, prob) in results]
        return extracted_text

    def extract_key_values(self, text_lines):
        """
        Busca patrones comunes en cierres Z (PoC).
        Esta función se irá refinando según los ejemplos reales.
        """
        data = {
            "num_cierre": None,
            "total_ventas": None,
            "impuesto": None
        }
        
        # Lógica de búsqueda simple (esto es muy dependiente del formato)
        for i, line in enumerate(text_lines):
            line_upper = line.upper()
            if "CIERRE" in line_upper:
                # Intentar buscar un número cerca
                print(f"Posible línea de cierre encontrada: {line}")
            
            if "TOTAL" in line_upper or "NETO" in line_upper:
                print(f"Posible línea de total encontrada: {line}")
                
        return data

if __name__ == "__main__":
    # Prueba rápida si se ejecuta directamente
    processor = OCRProcessor()
    # Aquí iría un path a una imagen de prueba
    # text = processor.process_image("ruta/a/imagen.jpg")
    # print(text)
