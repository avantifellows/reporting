import os
import requests
from fastapi.responses import StreamingResponse, HTMLResponse


def convert_template_to_pdf(template_response):
    """
    Convert a TemplateResponse to a PDF using the HTML-to-PDF server.

    Args:
        template_response: The TemplateResponse to convert

    Returns:
        StreamingResponse: The PDF response if successful
        HTMLResponse: An error response if conversion fails
    """
    html_content = template_response.body
    html_content = html_content.decode("utf-8")  # Decode bytes to string

    # Convert bytes to string if necessary
    if isinstance(html_content, bytes):
        html_content = html_content.decode()

    # Send HTML to PDF rendering service
    url = os.getenv("HTML_TO_PDF_SERVER_URL")
    response = requests.post(url, json={"html": html_content})

    # Check if the request was successful
    if response.status_code == 200:
        # Return the PDF as a streaming response
        return StreamingResponse(
            response.iter_content(chunk_size=10240),
            media_type="application/pdf",
        )
    else:
        return HTMLResponse(content="Error generating PDF", status_code=500)
