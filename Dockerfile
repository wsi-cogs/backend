FROM python:3.6

WORKDIR /cogs
ADD . .

RUN pip install -r requirements.txt

EXPOSE 8001
VOLUME /cogs/config/config.yaml

CMD python -OOm main