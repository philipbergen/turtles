FROM jenkins
USER root
COPY turtles /turtles
RUN apt-get update \
 && apt-get install -y git python-pip docker.io \
 && (cd /turtles; python setup.py install)
USER jenkins