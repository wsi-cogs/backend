FROM python:3.6

WORKDIR /cogs
ADD . .

RUN pip install -U pip wheel setuptools \
 && pip install -r requirements.base.txt

EXPOSE 8000
VOLUME /cogs/config.yaml

CMD ./start.sh
