FROM ubuntu

RUN apt-get update && apt-get install -y python
RUN apt-get install -y python-tk
RUN apt-get install -y python-pip
RUN pip install pillow

WORKDIR /
ADD . /

# ENV DISPLAY :0

CMD ["python", "gui.py"]