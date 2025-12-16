from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
import base64
import tempfile
import os

app = FastAPI()

class SVGRequest(BaseModel):
    svg_content: str

@app.get("/")
def read_root():
    return {"status": "SVG to PNG Converter is running", "engine": "Playwright"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/convert")
async def convert_svg_to_png(request: SVGRequest):
    try:
        # Create temporary HTML file with SVG
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_file:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        width: 1200px;
                        height: 1200px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        background: white;
                    }}
                    svg {{
                        width: 1200px !important;
                        height: 1200px !important;
                        max-width: 1200px;
                        max-height: 1200px;
                    }}
                </style>
            </head>
            <body>
                {request.svg_content}
            </body>
            </html>
            """
            html_file.write(html_content)
            html_path = html_file.name
        
        # Convert to PNG using Playwright async API
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={{'width': 1200, 'height': 1200}})
            await page.goto(f'file://{html_path}')
            
            # Wait for SVG to be fully loaded and rendered
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)  # Wait 2 seconds for rendering
            
            # Take screenshot with exact dimensions
            png_bytes = await page.screenshot(full_page=False)
            await browser.close()
        
        # Clean up
        os.unlink(html_path)
        
        # Convert to base64
        png_base64 = base64.b64encode(png_bytes).decode('utf-8')
        
        return {{"png_base64": png_base64}}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
