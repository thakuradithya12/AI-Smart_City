FROM python:3.12.16-slim-trixie
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils gdal-bin libgdal-dev libgeos-dev libproj-dev gcc && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt
COPY . /app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
