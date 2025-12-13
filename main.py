from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
from playwright.sync_api import sync_playwright
import tempfile
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SVG to PNG Converter")

class SVGRequest(BaseModel):
    svg_content: str

@app.get("/")
async def root():
    return {"status": "SVG to PNG Converter is running", "engine": "Playwright"}

@app.post("/convert")
async def convert_svg_to_png(request: SVGRequest):
    svg_path = None
    png_path = None
    
    try:
        logger.info("Iniciando conversión SVG→PNG con Playwright")
        
        # Crear archivo temporal para el HTML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_file:
            # Wrap SVG en HTML completo
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        svg {{
            display: block;
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
{request.svg_content}
</body>
</html>"""
            html_file.write(html_content)
            svg_path = html_file.name
        
        logger.info(f"HTML temporal creado: {svg_path}")
        
        # Crear archivo temporal para el PNG
        png_path = tempfile.mktemp(suffix='.png')
        
        # Convertir usando Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1200, 'height': 1200})
            
            # Cargar el HTML
            page.goto(f'file://{svg_path}')
            
            # Esperar a que el SVG se renderice completamente
            page.wait_for_load_state('networkidle')
            
            # Tomar screenshot con fondo blanco
            page.screenshot(
                path=png_path,
                full_page=True,
                omit_background=False
            )
            
            browser.close()
        
        logger.info(f"PNG generado: {png_path}")
        
        # Leer PNG y convertir a base64
        with open(png_path, 'rb') as png_file:
            png_bytes = png_file.read()
            png_base64 = base64.b64encode(png_bytes).decode('utf-8')
        
        logger.info(f"Conversión exitosa, tamaño: {len(png_bytes)} bytes")
        
        return {
            "png_base64": png_base64,
            "size_bytes": len(png_bytes)
        }
        
    except Exception as e:
        logger.error(f"Error en conversión: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    finally:
        # Limpiar archivos temporales
        if svg_path and os.path.exists(svg_path):
            os.unlink(svg_path)
        if png_path and os.path.exists(png_path):
            os.unlink(png_path)

@app.get("/health")
async def health():
    return {"status": "healthy"}
