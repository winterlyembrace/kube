FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir --prefix=/installer flask

FROM gcr.io/distroless/python3@sha256:17b27c84c985a53d0cd2adef4f196ca327fa9b6755369be605cf45533b4e700b
COPY --from=builder /installer /usr/local 
COPY app.py /app/app.py
WORKDIR /app
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD ["app.py"]
