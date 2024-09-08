# syntax=docker/dockerfile:1

FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /mkwpp/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
