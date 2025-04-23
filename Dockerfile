# Base image
FROM python:3.9

LABEL Pritam "pritam@avantifellows.org"

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
