FROM docker.io/python:3.12.11-slim-bookworm AS python

FROM python AS python-build-stage

RUN apt-get update && apt-get install --no-install-recommends -y \
  build-essential \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock* ./
COPY pynat/ ./pynat/

RUN uv venv /opt/venv
RUN uv pip install --python /opt/venv/bin/python -e ".[dev]"

FROM python AS python-run-stage

ARG APP_HOME=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install --no-install-recommends -y \
  curl \
  && curl -LsSf https://astral.sh/uv/install.sh | sh \
  && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

RUN apt-get update && apt-get install --no-install-recommends -y \
  sudo git bash-completion nano ssh

RUN groupadd --gid 1000 dev-user \
  && useradd --uid 1000 --gid dev-user --shell /bin/bash --create-home dev-user \
  && echo dev-user ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/dev-user \
  && chmod 0440 /etc/sudoers.d/dev-user

RUN apt-get update && apt-get install --no-install-recommends -y \
  libpq-dev \
  wait-for-it \
  gettext \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY --from=python-build-stage /opt/venv /opt/venv

COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint && chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start && chmod +x /start

COPY ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker && chmod +x /start-celeryworker

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat && chmod +x /start-celerybeat

COPY ./compose/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower && chmod +x /start-flower

COPY . ${APP_HOME}

ENTRYPOINT ["/entrypoint"]
