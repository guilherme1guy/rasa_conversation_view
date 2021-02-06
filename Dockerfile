FROM python:alpine

ADD . /code
WORKDIR /code

RUN pip install -r requirements.txt

CMD flask run --host=0.0.0.0
