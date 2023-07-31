SGPP
==============
***This project is part of my master thesis, Software Engineering, and Green IT at the VU Amsterdam and UVA***

**Author:** *Hugo Zwaan*
**Date:** *Feb 2023/ Aug 2023*

Serverless Graph Processing Platform is a program built using Kubernetes and Python. The program monitors a namespace for 'start' custom resources and when it finds new custom resources it adds a graph processing deployment to the cluster. The program cleans up after itself and the only setup for a deployment is the start custom resource. Via email, a notification is sent once the deployment is finished.

---------
<h2>links</h2>

HNS = https://github.com/kubernetes-sigs/hierarchical-namespaces/blob/master/docs/user-guide/how-to.md
HNS DOWNLOAD = https://github.com/kubernetes-sigs/hierarchical-namespaces/releases
HNS INFO = https://kubernetes.io/blog/2020/08/14/introducing-hierarchical-namespaces/
KOPF = https://kopf.readthedocs.io/en/stable/ 
HELM = https://helm.sh/docs/intro/install/


---------
<h2>Setup</h2>

* Install HELM
* Install KOPF *(or not and use main_no_kopf.py)*

* Create a Kubernetes cluster, that you can connect to.
* Apply the files found in yamls/setup ```kubectl apply -f [file]```
* Setup the mount point for the controller in ```python/creator``` on line 104-124 *(for azure only change 119-121)*
* Setup the monitoring values in ```helm/prometheus/values.yaml```
* Install the prometheus monitoring ```helm install -f helm/prometheus/[file] prometheus prometheus-community/prometheus```
* Start a control program ```python python/main_no_kopf.py``` or ```kopf run -n serverless-graphs python/main.py```
* The system is now up and running

---------
<h2>Structure</h2>

* `docker` contains the container templates for the spark worker and controller
* `helm/prometheus` contains the values file used to set up Prometheus
* `python` contains the scripts used to deploy the graph processing deployments
* `tests` contains the test suite used for the thesis
* `timestamps` contains the raw and processed data from the test suite
* `yamls` contains the setup and test suite yamls
