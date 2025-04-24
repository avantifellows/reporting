#!/usr/bin/env python3
"""
Script to test WeasyPrint integration by generating a test PDF
"""
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Generate a simple test PDF to validate WeasyPrint integration"""
    logger.info("Testing WeasyPrint integration...")

    # Print Python environment details
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"sys.path: {sys.path}")

    # Print environment variables
    logger.info(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not set')}")
    logger.info(f"FONTCONFIG_PATH: {os.environ.get('FONTCONFIG_PATH', 'Not set')}")
    logger.info(
        f"GDK_PIXBUF_MODULE_FILE: {os.environ.get('GDK_PIXBUF_MODULE_FILE', 'Not set')}"
    )
    logger.info(f"XDG_DATA_DIRS: {os.environ.get('XDG_DATA_DIRS', 'Not set')}")

    # Try importing WeasyPrint
    try:
        from weasyprint import HTML

        logger.info("WeasyPrint imported successfully!")

        # Generate a simple PDF
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WeasyPrint Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 50px; }
                h1 { color: #003366; }
                p { font-size: 14px; line-height: 1.5; }
                .date { color: #666666; font-style: italic; }
            </style>
        </head>
        <body>
            <h1>WeasyPrint Test Document</h1>
            <p class="date">Generated on: 2024-04-24</p>
            <p>This is a simple test document to verify that WeasyPrint is working correctly.</p>
            <p>If you can see this PDF, the integration is successful!</p>
        </body>
        </html>
        """

        # Create output directory if it doesn't exist
        output_dir = Path("./output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "weasyprint_test.pdf"

        # Generate the PDF
        logger.info(f"Generating PDF at {output_path}...")
        HTML(string=html_content).write_pdf(str(output_path))

        logger.info(f"PDF generated successfully at {output_path}")
        return True
    except ImportError as e:
        logger.error(f"Failed to import WeasyPrint: {e}")
        return False
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
