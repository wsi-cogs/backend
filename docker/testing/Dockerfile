FROM python:3.6

WORKDIR /cogs
ADD webapp/ .

RUN pip install -r requirements.auth.txt

EXPOSE 8000
VOLUME /cogs/config/test.yaml:/cogs/config.yaml

CMD python -OOm cogs.main
