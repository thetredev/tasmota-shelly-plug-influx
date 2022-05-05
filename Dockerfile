FROM python:3.10.4-alpine3.15

RUN adduser -D -u 5000 shelly

WORKDIR /home/shelly
USER shelly

COPY --chown=shelly:shelly ./requirements.txt ./

ENV PATH="${PATH}:/home/shelly/.local/bin"
RUN pip3 install --user -r requirements.txt && \
    rm -rf requirements.txt

COPY --chown=shelly:shelly ./shelly2influxdb.py ./
ENTRYPOINT [ "python3", "/home/shelly/shelly2influxdb.py" ]
