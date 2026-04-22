FROM python:3.13-trixie

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "src/kafka_dae_control/__init__.py"]
