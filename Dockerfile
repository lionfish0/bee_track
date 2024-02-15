# docker build . --tag bee_track:latest
FROM debian:buster-slim
COPY requirements.txt .
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install -r requirements.txt
