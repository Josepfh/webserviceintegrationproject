FROM python:3.11-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN uv sync --locked

EXPOSE 5000

CMD [".venv/bin/python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "run:app"]