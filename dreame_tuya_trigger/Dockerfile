ARG BUILD_FROM
FROM ${BUILD_FROM:-python:3.11-slim}

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/
COPY run.sh /run.sh
RUN chmod +x /run.sh

LABEL \
    io.hass.version="1.0.0" \
    io.hass.type="addon" \
    io.hass.arch="armhf|armv7|aarch64|i386|amd64"

CMD [ "/run.sh" ]
