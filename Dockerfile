FROM gcr.io/distroless/python3@sha256:17b27c84c985a53d0cd2adef4f196ca327fa9b6755369be605cf45533b4e700b

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

EXPOSE 5000

CMD ["./log_output.py"]
