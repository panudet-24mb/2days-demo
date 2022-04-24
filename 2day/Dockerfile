FROM tiangolo/uvicorn-gunicorn:python3.8
COPY requirements.txt /tmp/requirements.txt
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY ./python/app /python/app
CMD ["/start-reload.sh"]
