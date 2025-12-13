from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import cairosvg
import base64
from typing import Optional

# Crear app FastAPI
app = FastAPI(
    title="SVG to PNG Converter",
    description="Convierte SVG (Base64) a PNG (Base64) usando CairoSVG",
    version="1.0.0"
)

# Schema del request
class SVGInput(BaseModel):
    svg_base64: str
    output_width: Optional[int] = None
    output_height: Optional[int] = None

# Schema del response
class PNGOutput(BaseModel):
    png_base64: str
    message: str

@app.get("/")
async def root():
    return {
        "service": "SVG to PNG Converter",
        "status": "running",
        "endpoint": "/convert",
        "method": "POST"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/convert", response_model=PNGOutput)
async def convert_svg_to_png(data: SVGInput):
    try:
        # 1. Decodificar SVG desde Base64
        svg_bytes = base64.b64decode(data.svg_base64)
        
        # 2. Validar que sea SVG
        svg_text = svg_bytes.decode('utf-8')
        if '<svg' not in svg_text.lower():
            raise HTTPException(
                status_code=400,
                detail="El contenido no parece ser un SVG válido"
            )
        
        # 3. Convertir SVG a PNG (TODO EN MEMORIA)
        png_kwargs = {'bytestring': svg_bytes}
        
        # Agregar dimensiones si se especificaron
        if data.output_width:
            png_kwargs['output_width'] = data.output_width
        if data.output_height:
            png_kwargs['output_height'] = data.output_height
        
        png_bytes = cairosvg.svg2png(**png_kwargs)
        
        # 4. Codificar PNG a Base64
        png_base64 = base64.b64encode(png_bytes).decode('utf-8')
        
        return {
            "png_base64": png_base64,
            "message": "Conversión exitosa"
        }
        
    except base64.binascii.Error:
        raise HTTPException(
            status_code=400,
            detail="Error al decodificar Base64. Asegúrate de enviar SVG en Base64 válido"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al convertir SVG: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
