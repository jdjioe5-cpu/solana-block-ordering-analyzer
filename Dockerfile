FROM python:3.11-slim

WORKDIR /app

# Zero external pip dependencies required - runs purely on Python standard library
COPY analyzer/ /app/analyzer/
COPY tests/ /app/tests/

ENV PYTHONPATH=/app
ENV DRY_RUN=true
ENV MAX_SPEND_SOL=0.05

ENTRYPOINT ["python", "-m", "analyzer.cli"]
CMD ["--run", "--slots", "6"]
