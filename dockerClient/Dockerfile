FROM ubuntu

RUN apt-get update && apt-get install -y python
RUN apt-get install -y python-tk
RUN apt-get install -y python-pip
RUN pip install --upgrade pip
RUN pip install pillow netifaces

ADD . /

EXPOSE 11111

CMD ["python", "gui.py"]