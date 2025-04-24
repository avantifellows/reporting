import os
import base64
import logging
import sys
from typing import Union
from bs4 import BeautifulSoup
from fastapi.responses import StreamingResponse, HTMLResponse
from io import BytesIO

# Setup detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug environment information
logger.info(f"Python version: {sys.version}")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
logger.info(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not set')}")
logger.info(f"FONTCONFIG_PATH: {os.environ.get('FONTCONFIG_PATH', 'Not set')}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir('.')}")

# Try to locate WeasyPrint module
try:
    # Add /opt directories to sys.path if not already there
    opt_paths = [
        "/opt/python/lib/python3.13/site-packages",
        "/opt/python/lib/python3.9/site-packages",
        "/var/task",
        "/opt/python",
    ]

    for path in opt_paths:
        if os.path.exists(path) and path not in sys.path:
            logger.info(f"Adding path to sys.path: {path}")
            sys.path.insert(0, path)

    # List directories to debug
    if os.path.exists("/opt"):
        logger.info(f"/opt contents: {os.listdir('/opt')}")

    if os.path.exists("/opt/python"):
        logger.info(f"/opt/python contents: {os.listdir('/opt/python')}")

    # Import WeasyPrint with fallback
    try:
        from weasyprint import HTML

        WEASYPRINT_AVAILABLE = True
        logger.info("WeasyPrint successfully imported")
        logger.info(f"WeasyPrint path: {getattr(HTML, '__module__', 'unknown')}")
    except ImportError as e:
        logger.error(f"Error importing WeasyPrint: {str(e)}")
        logger.error(
            "Make sure the WeasyPrint layer is properly attached to the Lambda function"
        )
        WEASYPRINT_AVAILABLE = False
        HTML = None
except Exception as e:
    logger.error(f"Error during module setup: {str(e)}")
    WEASYPRINT_AVAILABLE = False
    HTML = None


def convert_template_to_pdf(
    template_response,
    debug: bool = False,
) -> Union[StreamingResponse, HTMLResponse]:
    """
    Convert a TemplateResponse to a PDF document using WeasyPrint.

    Args:
        template_response: The template response to convert to PDF.
        debug (bool): If True, return the HTML instead of converting to PDF.

    Returns:
        StreamingResponse: A streaming response with the PDF content.
        HTMLResponse: The HTML content if debug=True.
    """
    # Get the HTML content from the template response
    html_content = template_response.body.decode()

    # If debug is True, return the HTML content
    if debug:
        return HTMLResponse(content=html_content, status_code=200)

    # Check if WeasyPrint is available
    if not WEASYPRINT_AVAILABLE:
        logger.error("WeasyPrint is not available. Cannot convert HTML to PDF.")
        return HTMLResponse(
            content="<h1>Error: PDF conversion is not available</h1><p>WeasyPrint library could not be loaded.</p>",
            status_code=500,
        )

    # Parse the HTML and inline CSS
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all CSS links and inline them
    for link in soup.find_all("link", rel="stylesheet"):
        if link.get("href"):
            css_path = link.get("href")

            # Try different file paths
            css_file_paths = [
                f"static{css_path}",
                f"static/{css_path}",
                f"{css_path}",
                f"app/static{css_path}",
                f"app/static/{css_path}",
            ]

            css_content = None
            for file_path in css_file_paths:
                try:
                    if os.path.exists(file_path):
                        with open(file_path, "r") as f:
                            css_content = f.read()
                            break
                except Exception as e:
                    logger.warning(f"Error reading CSS file {file_path}: {str(e)}")

            if css_content:
                # Replace the link with a style tag
                new_style = soup.new_tag("style")
                new_style.string = css_content
                link.replace_with(new_style)

    # Find all img tags and convert them to base64
    for img in soup.find_all("img"):
        if img.get("src"):
            img_path = img.get("src")

            # Try different file paths
            img_file_paths = [
                f"static{img_path}",
                f"static/{img_path}",
                f"{img_path}",
                f"app/static{img_path}",
                f"app/static/{img_path}",
            ]

            img_content = None
            for file_path in img_file_paths:
                try:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            img_content = f.read()
                            break
                except Exception as e:
                    logger.warning(f"Error reading image file {file_path}: {str(e)}")

            if img_content:
                # Get the image type
                img_type = img_path.split(".")[-1].lower()
                img_type = "jpeg" if img_type == "jpg" else img_type

                # Convert the image to base64
                base64_img = base64.b64encode(img_content).decode()

                # Update the src attribute
                img["src"] = f"data:image/{img_type};base64,{base64_img}"

    # Get the updated HTML content
    html_content = str(soup)

    # Convert to PDF using WeasyPrint
    try:
        logger.info("Starting PDF generation with WeasyPrint...")
        pdf_buffer = BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        logger.info("PDF generation successful!")

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline; filename=report.pdf"},
        )
    except Exception as e:
        logger.error(f"Error converting HTML to PDF with WeasyPrint: {str(e)}")
        raise Exception(f"Failed to convert HTML to PDF: {str(e)}")
