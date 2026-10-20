FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && groupadd -g 10001 platform && useradd -u 10001 -g 10001 -r -s /usr/sbin/nologin platform
COPY src ./src
USER 10001:10001
CMD ["uvicorn","agent_platform.api:app","--host","0.0.0.0","--port","8000"]
