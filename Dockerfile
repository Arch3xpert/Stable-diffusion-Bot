FROM python:latest
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --upgrade pip
WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]