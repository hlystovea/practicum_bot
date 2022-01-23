FROM python:3.9-alpine
WORKDIR /practicum_bot
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
