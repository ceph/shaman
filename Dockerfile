FROM python:3.11-alpine
EXPOSE 8080
ENV TZ="UTC"
RUN apk add curl tzdata && \
  pip install -U pip

# Install dependencies:
COPY requirements.txt .
ADD . /shaman
RUN pip3 install -r requirements.txt
RUN pip3 install cherrypy
RUN pip3 install /shaman/.

# Run the application:
COPY config/ /shaman/config
COPY alembic.ini /shaman/alembic.ini
COPY container_start.sh /shaman/container_start.sh
WORKDIR /shaman
CMD sh container_start.sh