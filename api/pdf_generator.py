import io
from fpdf import FPDF
import requests
from io import BytesIO
from PIL import Image

class PDFReport(FPDF):
    def __init__(self, company_name, logo_url=None):
        super().__init__()
        self.company_name = company_name
        self.logo_url = logo_url

    def header(self):
        # Logo
        if self.logo_url:
            try:
                response = requests.get(self.logo_url, timeout=5)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    img_path = "/tmp/temp_logo.png"
                    img.save(img_path)
                    self.image(img_path, 10, 8, 33)
            except Exception as e:
                print(f"Error loading logo: {e}")
        
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, f'{self.company_name} - Reporte de Cierre Z', 0, 0, 'C')
        # Line break
        self.ln(20)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

def generate_cierre_pdf(cierre_data, company_data, branch_data):
    pdf = PDFReport(company_data['name'], company_data.get('logo_url'))
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    # Datos del Cierre
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Detalles del Cierre', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    pdf.cell(50, 10, f"Sucursal: {branch_data['name']}", 0, 0)
    pdf.cell(50, 10, f"Fecha: {cierre_data['date_closed']}", 0, 0)
    pdf.cell(50, 10, f"No. Z: {cierre_data['z_number']}", 0, 1)
    pdf.cell(50, 10, f"Estado Contable: {'Cuadrado' if cierre_data['status'] == 'balanced' else 'Descuadrado'}", 0, 0)
    pdf.cell(50, 10, f"Estado Flujo: {cierre_data['workflow_status'].upper()}", 0, 1)
    
    pdf.ln(10)
    
    # Resumen Financiero
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Resumen Financiero', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    pdf.cell(80, 10, f"Ventas Gravables: ${cierre_data['taxable_sales']:.2f}", 0, 1)
    pdf.cell(80, 10, f"Ventas Exentas: ${cierre_data['exempt_sales']:.2f}", 0, 1)
    pdf.cell(80, 10, f"Impuestos: ${cierre_data['tax_amount']:.2f}", 0, 1)
    pdf.cell(80, 10, f"Total de Ventas: ${cierre_data['total_sales']:.2f}", 0, 1)
    pdf.cell(80, 10, f"Total en Caja/Bancos: ${cierre_data['total_receipt']:.2f}", 0, 1)
    pdf.cell(80, 10, f"Diferencia: ${cierre_data['difference_amount']:.2f}", 0, 1)
    
    pdf.ln(10)
    
    # Métodos de Pago
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Detalle de Pagos', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    for payment in cierre_data.get('payments', []):
        pdf.cell(80, 10, f"{payment['payment_method_name']}: ${payment['amount']:.2f}", 0, 1)
    
    # Agregar evidencias fotográficas
    evidences = [
        ("Tiquete Z", cierre_data.get('image_url')),
        ("Recibo POS", cierre_data.get('pos_receipt_url')),
        ("Comprobante Depósito", cierre_data.get('deposit_receipt_url'))
    ]
    
    for title, url in evidences:
        if url:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'Evidencia: {title}', 0, 1, 'C')
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    img_path = f"/tmp/temp_ev_{title.replace(' ', '_')}.png"
                    img.save(img_path)
                    
                    # Calcular dimensiones para ajustar a la página
                    pdf_w = 210 - 20
                    pdf_h = 297 - 40
                    img_w, img_h = img.size
                    ratio = min(pdf_w / img_w, pdf_h / img_h)
                    new_w = img_w * ratio
                    new_h = img_h * ratio
                    
                    pdf.image(img_path, x=(210 - new_w) / 2, y=30, w=new_w, h=new_h)
            except Exception as e:
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, f'No se pudo cargar la imagen: {e}', 0, 1, 'C')

    # Guardar en buffer
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)
