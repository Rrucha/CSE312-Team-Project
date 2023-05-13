FROM python:3.8.2

ENV HOME /root
WORKDIR /root

COPY . .

RUN pip install pymongo
RUN pip install Flask
RUN pip install Flask_SocketIO
RUN pip install gevent-websocket
RUN pip install bcrypt

EXPOSE 8000

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait

CMD /wait && python3 -u run.py