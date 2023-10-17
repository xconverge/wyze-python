FROM python:3.11

COPY requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN pip install -r requirements.txt
COPY . /opt/app
CMD ["python", "-u", "/opt/app/app.py"]
