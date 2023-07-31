import os
import re
import subprocess
import time

SPARK_MASTER = 7077
SPARK_WORKER = 8081
SPARK_WEBUI = 8080

SPARK_DRIVER_PORT = 33595

GET_MASTER_IP = (
    lambda sub_ns: f"""kubectl get pod spark-master -n {sub_ns} --template '{"{{.status.podIP}}"}'"""
)
IS_IPV4 = lambda ip: re.search(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", ip)


def via_file(
    ns: str,
    sub_ns: str,
    nr_workers: int,
    crd_name: str,
    file: str,
    user_email: str,
    tenant: str,
    offset: int = 0,
):
    driver: int = SPARK_DRIVER_PORT + offset

    # Create Sub namespace
    subprocess.run(f"kubectl hns create {sub_ns} -n {ns}", shell=True)

    # Need to wait a bit for subnamespace because other resources can not find it
    time.sleep(2)

    part_one = f"""
apiVersion: v1
kind: Pod
metadata:
  name: spark-master
  namespace: {sub_ns}
spec:
  containers:
    - name: spark-master
      image: hug0z/serverless-spark:latest
      env:
        - name: SPARK_MODE
          value: master
        - name: SPARK_RPC_AUTHENTICATION_ENABLED
          value: "no"
        - name: SPARK_RPC_ENCRYPTION_ENABLED
          value: "no"
        - name: SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED
          value: "no"
        - name: SPARK_SSL_ENABLED
          value: "no"
        - name: SPARK_USER
          value: spark
      ports:
        - containerPort: {SPARK_MASTER}
        - containerPort: {SPARK_WEBUI}   
        - containerPort: {driver}  

---

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: spinupcontainers-{offset}
rules:
  - apiGroups: ["", "*"]
    resources: ["*"]
    verbs:
      - create
      - get
      - watch
      - list

---

apiVersion: v1
kind: ServiceAccount
metadata:
  name: spinupcontainers-{offset}
  namespace: {sub_ns}         

---

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: spinupcontainers-{offset}
subjects:
  - kind: ServiceAccount
    name: spinupcontainers-{offset}
    namespace: {sub_ns}  
roleRef:
  kind: ClusterRole
  name: spinupcontainers-{offset}
  apiGroup: rbac.authorization.k8s.io

---

kind: PersistentVolume
apiVersion: v1
metadata:
  name: "pv-{sub_ns}"
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - "ReadWriteMany"
  persistentVolumeReclaimPolicy: Retain
  csi:
    driver: file.csi.azure.com
    readOnly: false
    volumeHandle: k8s
    volumeAttributes:
      storageAccount: "k8sfilestorage"
      resourceGroup: "k8s_group"
      shareName: "tenants"
  mountOptions:
    - dir_mode=0777
    - file_mode=0777

---

kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: "pvc-azuredisk"
  namespace: {sub_ns}
spec:
  accessModes:
    - "ReadWriteMany"
  storageClassName: ""
  volumeName: "pv-{sub_ns}"
  resources:
    requests:
      storage: "2Gi"
"""
    with open(f"temp_{sub_ns}.yaml", "w") as outfile:
        outfile.write(part_one)
    subprocess.run(f"kubectl apply -f temp_{sub_ns}.yaml", shell=True)

    no_master_ip: bool = True
    while no_master_ip:
        master_ip: str = str(subprocess.getoutput(GET_MASTER_IP(sub_ns))).replace("'", "")

        if IS_IPV4(master_ip):
            no_master_ip = False
        else:
            time.sleep(2)

    part_two = f"""
kind: Deployment
apiVersion: apps/v1
metadata:
  name: spark-worker
  namespace: {sub_ns}
spec:
  replicas: {nr_workers}
  selector:
    matchLabels:
      component: spark-worker
  template:
    metadata:
      labels:
        component: spark-worker
    spec:
      securityContext:
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
        - name: spark-worker
          image: hug0z/serverless-spark:latest
          env:
            - name: SPARK_MODE
              value: worker
            - name: SPARK_MASTER_URL
              value: "spark://{master_ip}:{SPARK_MASTER}"
            - name: SPARK_WORKER_MEMORY
              value: "4G"
            - name: SPARK_WORKER_CORES
              value: "2"
            - name: SPARK_RPC_AUTHENTICATION_ENABLED
              value: "no"
            - name: SPARK_RPC_ENCRYPTION_ENABLED
              value: "no"
            - name: SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED
              value: "no"
            - name: SPARK_SSL_ENABLED
              value: "no"
            - name: SPARK_USER
              value: spark
          ports:
            - containerPort: {SPARK_WORKER}
---

apiVersion: v1
kind: Pod
metadata:
  name: controller
  namespace: {sub_ns}
spec:
  containers:
    - name: controller
      image: hug0z/serverless-graphs:latest
      env:
        - name: SUB_NAMESPACE
          value: "{sub_ns}"
        - name: START
          value: "{crd_name}"
        - name: SPARK_MASTER_URL
          value: "spark://{master_ip}:{SPARK_MASTER}"
        - name: DRIVER
          value: "{driver}"
        - name: FILE
          value: {file}
        - name: SELF
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: EMAIL
          value: {user_email}
      ports:
        - containerPort: {driver}
      volumeMounts:
        - mountPath: /python/mount
          name: volume-graph
          subPath: {tenant}
  volumes:
    - name: volume-graph
      persistentVolumeClaim:
        claimName: pvc-azuredisk
  serviceAccountName: spinupcontainers-{offset}
"""

    with open(f"temp_{sub_ns}.yaml", "w") as outfile:
        outfile.write(part_two)

    subprocess.run(f"kubectl apply -f temp_{sub_ns}.yaml", shell=True)
    os.remove(f"temp_{sub_ns}.yaml")
