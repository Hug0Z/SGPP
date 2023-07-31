import os
import subprocess
import time
from importlib import import_module
from inspect import getmembers, isfunction

from pyspark.sql import SparkSession

os.environ[
    "PYSPARK_SUBMIT_ARGS"
] = "--packages graphframes:graphframes:0.8.2-spark3.2-s_2.12 --driver-memory 4g --executor-memory 4g pyspark-shell"

import warnings

# ENV given by deployment
NAMESPACE = "serverless-graphs"
SUB_NAMESPACE: str = os.environ.get("SUB_NAMESPACE")
START: str = os.environ.get("START")

OWN_IP: str = os.environ.get("SELF")
SPARK_MASTER_URL: str = os.environ.get("SPARK_MASTER_URL")
DRIVER: str = os.environ.get("DRIVER")
OPERATION: str = os.environ.get("FILE")

EMAIL: str = os.environ.get("EMAIL")
warnings.warn(str(EMAIL))

MOUNT_PATH: str = "python/mount"

code: int = 0
# -------------------Graph stuff---------------------
try:
    warnings.warn(str(SPARK_MASTER_URL))
    spark: SparkSession = (
        SparkSession.builder.master(SPARK_MASTER_URL)
        .config("spark.driver.host", OWN_IP)
        .config("spark.driver.bindAddress", OWN_IP)
        .config("spark.driver.port", DRIVER)
        .appName(f"Program")
        .enableHiveSupport()
        .getOrCreate()
    )
except Exception as e:
    code = 500
    warnings.warn(e)

if code == 0:
    try:
        tenant_program = import_module(OPERATION)
        warnings.warn(str(getmembers(tenant_program, isfunction)))
        if any([_[0] == "main" for _ in getmembers(tenant_program, isfunction)]):
            tenant_program.main(spark, MOUNT_PATH)
            code = 200
        else:
            code = 400
            print("error: no function called main")
    except Exception as e:
        code = 400
        warnings.warn(str(e))
        with open(f"{MOUNT_PATH}/error_main.txt", "a") as outfile:
            outfile.write(str(e))


# -------------------Start cleanup-------------------
data = f"""
apiVersion: softwareengineering.solvinity.com/v1
kind: finish-g
metadata:
  name: {START}
  namespace: {NAMESPACE}
spec:
  Start: {START}
  SubNamespace: {SUB_NAMESPACE}
  UserEmail: {EMAIL}
  ResultCode: {code}
"""

with open("temp.yaml", "w") as outfile:
    outfile.write(data)

subprocess.run(f"kubectl apply -f temp.yaml", shell=True)
