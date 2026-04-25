from gsheets_api import GoogleSheetsAPI
from ocr_processor import OCRProcessor
import os

def test_flow(image_drive_id=None, image_name=None):
    # 1. Inicializar APIs
    try:
        gsheets = GoogleSheetsAPI(credentials_file='credentials.json')
    except FileNotFoundError:
        print("Error: No se encontró credentials.json. Asegúrate de tenerlo en la carpeta raíz.")
        return

    ocr = OCRProcessor()

    # 2. Obtener ID de la imagen si solo tenemos el nombre
    if not image_drive_id and image_name:
        print(f"Buscando archivo por nombre: {image_name}...")
        image_drive_id = gsheets.find_file_by_name(image_name)

    if not image_drive_id:
        print("No se encontró el ID de la imagen. Proporciona uno o un nombre válido.")
        return

    # 3. Descargar imagen
    temp_path = "temp_ocr_image.jpg"
    gsheets.download_file(image_drive_id, temp_path)

    # 4. Procesar con OCR
    if os.path.exists(temp_path):
        text_lines = ocr.process_image(temp_path)
        print("\n--- TEXTO EXTRAÍDO ---")
        for line in text_lines:
            print(line)
        print("----------------------\n")
        
        # Limpieza
        # os.remove(temp_path)
    else:
        print("Fallo la descarga de la imagen.")

if __name__ == "__main__":
    # Ejemplo de uso (El usuario debería proporcionar un ID o nombre real para probar)
    # test_flow(image_name="20240221_123456.jpg") 
    print("Script listo. Para probarlo, llama a test_flow con un ID de imagen de Drive.")
