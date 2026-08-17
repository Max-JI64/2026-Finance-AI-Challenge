FROM python:3.13.1-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /service

COPY requirements-runtime.txt ./
RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY app ./app
COPY src ./src
COPY scripts/build_re_stage7_examples.py ./scripts/build_re_stage7_examples.py
COPY config ./config
COPY artifacts/re_stage5_lightgbm_quantile ./artifacts/re_stage5_lightgbm_quantile
COPY data/samples/re_stage7 ./data/samples/re_stage7
COPY data/processed_re/re_stage8 ./data/processed_re/re_stage8
COPY data/processed_re/policy/re_stage2 ./data/processed_re/policy/re_stage2
COPY data/processed_re/policy/re_stage8_2 ./data/processed_re/policy/re_stage8_2
COPY reports/stage6 ./reports/stage6
COPY rag/index/policy_re8.sqlite3 ./rag/index/policy_re8.sqlite3

RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /service
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health', timeout=4).read()"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
