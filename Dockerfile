# docker build . --tag bee_track:latest
# docker run bee_track:latest
# docker run --rm -it --entrypoint bash bee_track:latest
# https://docs.docker.com/develop/develop-images/instructions/
FROM debian:bookworm-slim
# Install dependencies
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    python3.11 -m pip install --break-system-packages --requirement /tmp/requirements.txt

# Install app
COPY . /opt/bee_track

# Configure service
WORKDIR /opt/bee_track/
CMD python3 -m bee_track.core
