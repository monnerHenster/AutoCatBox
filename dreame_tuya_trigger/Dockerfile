# 追觅涂鸦触发 add-on（中国区涂鸦 Pulsar + excretion_time_day 触发追觅）
ARG BUILD_FROM
FROM ${BUILD_FROM:-python:3.11-slim}

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/
COPY run.sh /run.sh
RUN chmod +x /run.sh

LABEL \
    io.hass.type="addon" \
    io.hass.arch="armhf|aarch64|i386|amd64"

CMD [ "/run.sh" ]
