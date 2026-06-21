FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the model weights into the image at build time so inference doesn't
# need internet access.
RUN python -m monai.bundle download \
    --name spleen_ct_segmentation \
    --bundle_dir /opt/monai/bundles

COPY segment.py .

ENTRYPOINT ["python", "segment.py"]
