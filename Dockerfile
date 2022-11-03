# Base image
FROM python:3.9

LABEL Pritam "pritam@avantifellows.org"

WORKDIR /code

COPY requirements.txt /code/requirements.txt
ADD generate_table /app

RUN pip install -r /code/requirements.txt

COPY ./app /code

EXPOSE 80

# RUN python generate_table
# CMD ["python", "app/main.py"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050", "--reload"]
