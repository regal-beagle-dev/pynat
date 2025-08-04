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
RUN uv pip install --python /opt/venv/bin/python -e ".[prod]"

FROM python AS python-run-stage

ARG APP_HOME=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR ${APP_HOME}

RUN addgroup --system django \
  && adduser --system --ingroup django django

RUN apt-get update && apt-get install --no-install-recommends -y \
  libpq-dev \
  gettext \
  wait-for-it \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY --from=python-build-stage /opt/venv /opt/venv

COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint && chmod +x /entrypoint

COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start && chmod +x /start

COPY --chown=django:django ./compose/production/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker && chmod +x /start-celeryworker

COPY --chown=django:django ./compose/production/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat && chmod +x /start-celerybeat

COPY --chown=django:django ./compose/production/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower && chmod +x /start-flower

COPY --chown=django:django . ${APP_HOME}
RUN mkdir -p ${APP_HOME}/pynat/media
RUN chown -R django:django ${APP_HOME}

USER django

RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  python manage.py compilemessages

ENTRYPOINT ["/entrypoint"]
