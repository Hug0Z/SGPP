FROM bitnami/spark:3.3

ADD graphframes-0.8.2-spark3.2-s_2.12.jar /opt/bitnami/spark/jars/

ENTRYPOINT ["pyspark --packages graphframes:graphframes:0.8.2-spark3.2-s_2.12 --jars graphframes-0.8.2-spark3.2-s_2.12.jar"]