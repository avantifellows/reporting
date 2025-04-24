import os
import sys
import json


def handler(event, context):
    """Test handler to debug WeasyPrint layer issues"""
    result = {
        "status": "unknown",
        "environment": {
            "python_version": sys.version,
            "executable": sys.executable,
            "sys_path": sys.path,
            "ld_library_path": os.environ.get("LD_LIBRARY_PATH", "Not set"),
            "fontconfig_path": os.environ.get("FONTCONFIG_PATH", "Not set"),
            "gdk_pixbuf_module_file": os.environ.get(
                "GDK_PIXBUF_MODULE_FILE", "Not set"
            ),
            "xdg_data_dirs": os.environ.get("XDG_DATA_DIRS", "Not set"),
        },
        "import_test": {},
    }

    # Test importing WeasyPrint
    try:
        import weasyprint

        result["import_test"]["weasyprint"] = {
            "status": "success",
            "version": getattr(weasyprint, "__version__", "unknown"),
            "path": getattr(weasyprint, "__file__", "unknown"),
        }
    except ImportError as e:
        result["import_test"]["weasyprint"] = {"status": "failed", "error": str(e)}

    # Test importing HTML from WeasyPrint
    try:

        result["import_test"]["weasyprint_html"] = {"status": "success"}
    except ImportError as e:
        result["import_test"]["weasyprint_html"] = {"status": "failed", "error": str(e)}

    # List directories in /opt to see layer contents
    try:
        opt_contents = os.listdir("/opt")
        result["opt_directory"] = opt_contents
    except Exception as e:
        result["opt_directory"] = f"Error listing /opt: {str(e)}"

    # If /opt/lib exists, list its contents too
    if os.path.exists("/opt/lib"):
        try:
            result["opt_lib_directory"] = os.listdir("/opt/lib")
        except Exception as e:
            result["opt_lib_directory"] = f"Error listing /opt/lib: {str(e)}"

    return {"statusCode": 200, "body": json.dumps(result, indent=2)}
