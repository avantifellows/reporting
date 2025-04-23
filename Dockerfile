# Base image
FROM python:3.9

LABEL Pritam "pritam@avantifellows.org"

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt /code/requirements.txt
ADD generate_table /app

# Update pip first, then install with no cache and fix dependency resolution
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

COPY ./app /code

EXPOSE 80

# RUN python generate_table
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050", "--reload"]
