FROM python:3.10.4-alpine3.15

RUN adduser -D -u 5000 shelly

WORKDIR /home/shelly
USER shelly

COPY --chown=shelly:shelly . ./

ENV PATH="${PATH}:/home/shelly/.local/bin"
RUN pip3 install --user -r requirements.txt

ENTRYPOINT [ "python3", "/home/shelly/shelly-to-influxdb.py" ]
