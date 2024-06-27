FROM python:3.11-slim

WORKDIR /code
ADD ./pyproject.toml ./pyproject.toml
RUN pip install --upgrade pip && pip install --no-cache-dir .
ADD ./app ./app
ADD ./pyproject.toml ./app/pyproject.toml

WORKDIR /code/app

CMD ["python3", "."]