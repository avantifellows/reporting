# Base image
FROM python:3.9

LABEL Pritam "pritam@avantifellows.org"

WORKDIR /app

COPY requirements.txt /app/requirements.txt
ADD generate_table /app

RUN pip install -r /app/requirements.txt

COPY . /app

EXPOSE 80

# RUN python generate_table
CMD ["python", "app/main.py"]
