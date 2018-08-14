FROM python:3.6

WORKDIR /cogs
ADD . .

RUN pip install -U pip wheel setuptools \
 && pip install -r requirements.dev.txt

EXPOSE 8000
VOLUME /cogs/config/dev.yaml:/cogs/config.yaml

CMD python -m cogs.main
