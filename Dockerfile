FROM python:3
WORKDIR /app
EXPOSE 9090

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY raiderio_exporter/ raiderio_exporter/

CMD ["gunicorn", "-b", "0.0.0.0:9090", "--access-logfile", "-", "raiderio_exporter.app:app"]
