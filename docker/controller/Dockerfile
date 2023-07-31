FROM openjdk:11

COPY --from=lachlanevenson/k8s-kubectl:latest /usr/local/bin/kubectl /usr/local/bin/kubectl

RUN apt-get update && \
    apt-get install python3.9 && \
    apt-get install -y python3-pip;

ENV PYTHONUNBUFFERED=0

# ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/
# RUN export JAVA_HOME

RUN python3 - m pip install --upgrade pip

ADD req.txt /tmp/

RUN pip install -r /tmp/req.txt

RUN mkdir -p /python/

COPY . .

CMD ["python3", "/python/main.py"]