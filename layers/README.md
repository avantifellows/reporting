# Lambda Layers

This directory contains Lambda layers for the application.

## WeasyPrint Layer

The WeasyPrint layer contains all necessary dependencies to run WeasyPrint in an AWS Lambda environment.

### Layer Source

The WeasyPrint layer is sourced from the [kotify/cloud-print-utils](https://github.com/kotify/cloud-print-utils) project, which provides a pre-built Lambda layer with all dependencies properly configured.

### Required Environment Variables

When using the WeasyPrint layer, set these environment variables in your Lambda function:

```
LD_LIBRARY_PATH: /opt/lib
FONTCONFIG_PATH: /opt/fonts
GDK_PIXBUF_MODULE_FILE: /opt/lib/loaders.cache
XDG_DATA_DIRS: /opt/lib
```

### Manual Layer Installation

If you need to manually publish the layer:

```bash
aws lambda publish-layer-version \
  --layer-name WeasyPrintLayer \
  --zip-file fileb://weasyprint-layer-python3.9-x86_64.zip \
  --compatible-runtimes python3.9 \
  --region <your-region>
```
