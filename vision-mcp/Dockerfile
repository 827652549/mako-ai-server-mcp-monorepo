FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

COPY . .

# PORT 由 Render 注入，本地默认 8001
ENV PORT=8001

EXPOSE $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-config none
