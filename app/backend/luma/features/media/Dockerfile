FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pypdf==6.21.4 Pillow==13.0.0
WORKDIR /processor
COPY processor.py /processor/processor.py
USER 65534:65534
ENTRYPOINT ["python", "-I", "/processor/processor.py"]
