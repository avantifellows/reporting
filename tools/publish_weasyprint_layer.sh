#!/bin/bash
# Script to manually publish or update the WeasyPrint layer in AWS Lambda
# Usage: ./publish_weasyprint_layer.sh [region]

set -e

# Default to ap-south-1 if no region provided
REGION=${1:-ap-south-1}
LAYER_NAME="WeasyPrintLayer"

echo "Checking for WeasyPrint layer in region: $REGION"

# Create layers directory if it doesn't exist
mkdir -p layers

# Download WeasyPrint layer from GitHub releases
echo "Downloading WeasyPrint layer from GitHub releases..."
curl -L -o layers/weasyprint-layer.zip \
  https://github.com/kotify/cloud-print-utils/releases/download/weasyprint-65.1/weasyprint-layer-python3.13-x86_64.zip

# Check if layer exists
LAYER_VERSION=$(aws lambda list-layer-versions --layer-name $LAYER_NAME --region $REGION --query 'LayerVersions[0].LayerVersionArn' --output text 2>/dev/null || echo "")

if [ -z "$LAYER_VERSION" ] || [ "$LAYER_VERSION" == "None" ]; then
  echo "Publishing new WeasyPrint layer..."
  LAYER_VERSION=$(aws lambda publish-layer-version \
    --region $REGION \
    --layer-name $LAYER_NAME \
    --zip-file fileb://layers/weasyprint-layer.zip \
    --compatible-runtimes python3.9 python3.13 \
    --compatible-architectures x86_64 \
    --description "WeasyPrint for PDF generation (Python 3.13 layer for Python 3.9 runtime)" \
    --query 'LayerVersionArn' \
    --output text)

  echo "Layer published successfully!"
else
  echo "Updating existing WeasyPrint layer..."
  LAYER_VERSION=$(aws lambda publish-layer-version \
    --region $REGION \
    --layer-name $LAYER_NAME \
    --zip-file fileb://layers/weasyprint-layer.zip \
    --compatible-runtimes python3.9 python3.13 \
    --compatible-architectures x86_64 \
    --description "WeasyPrint for PDF generation (Python 3.13 layer for Python 3.9 runtime)" \
    --query 'LayerVersionArn' \
    --output text)

  echo "Layer updated successfully!"
fi

echo "WeasyPrint Layer ARN: $LAYER_VERSION"

# Instructions for next steps
echo "
To use this layer manually in the AWS console:
1. Go to your Lambda function
2. Scroll down to the 'Layers' section
3. Click 'Add a layer'
4. Select 'Specify an ARN'
5. Enter the ARN: $LAYER_VERSION
6. Click 'Add'

Make sure your Lambda has these environment variables:
- LD_LIBRARY_PATH: /opt/lib
- FONTCONFIG_PATH: /opt/fonts
- GDK_PIXBUF_MODULE_FILE: /opt/lib/loaders.cache
- XDG_DATA_DIRS: /opt/lib
- PYTHONPATH: /var/runtime:/var/task:/opt/python/lib/python3.13/site-packages
"
