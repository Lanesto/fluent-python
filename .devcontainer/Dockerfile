FROM python:3.9

RUN apt update && apt install -y \
        nginx \
    && rm -rf /var/lib/apt/lists/*

COPY ./.devcontainer/requirements.txt /
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt
