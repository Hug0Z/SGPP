import os
import smtplib
import ssl
import subprocess
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import kopf
from dotenv import load_dotenv

sys.path.append("../")
import creator as c
import functions as f

load_dotenv()

NAMESPACE = "serverless-graphs"
DELETE_SUB_NAMESPACE = lambda child, parent: f"kubectl delete subns {child} -n {parent}"
DELETE_START = lambda obj: f"kubectl delete start {obj} -n {NAMESPACE}"
DELETE_FINISH = lambda obj: f"kubectl delete finish {obj} -n {NAMESPACE}"
DELETE_PV = lambda pv: f"kubectl delete pv {pv}"

SMTP_SERVER = "smtp.gmail.com"
PROGRAM_EMAIL = os.getenv("EMAIL")
PROGRAM_EMAIL_PASSWORD = os.getenv("PASSWORD")

# Counters the number of runs, loops around at 100
counter = 2

TESTING = True


@kopf.on.create("serverless-graphs")
def creating_objects(spec, body, **kwargs):
    print("creating")
    global counter
    timestamps = [f.create_timestamp("start creation")]

    # Setup generics
    crd_name: str = str(body).split("name")[1][3:-3]
    tenant: str = str(spec.get("Tenant")).lower()
    user: str = str(spec.get("User")).lower()
    user_email: str = spec.get("UserEmail")

    # Setup run specifics
    nrWorkers: int = spec.get("NrWorkers", 2)
    run_id: int = counter
    file: str = f"mount.{spec.get('GraphLocation')}"
    execution_name: str = f"{tenant}-{user}-{run_id}"

    # Update counter
    counter = counter + 1 if counter < 100 else 0
    
    # Create all objects
    c.via_file(
        NAMESPACE,
        execution_name,
        nrWorkers,
        crd_name,
        file,
        user_email,
        str(spec.get("Tenant")),
        counter,
    )

    # Create timestamp file
    timestamps.append(f.create_timestamp("finish creation"))
    timestamps.append(f.create_timestamp("start execution"))
    f.add_stamps(execution_name, timestamps, header=True)

    return {
        "execution": execution_name,
    }


@kopf.on.create("finish-graph")
def clearing_objects(spec, **kwargs):
    print("cleaning")
    # Get variables
    start_obj: str = spec.get("Start")
    subns: str = spec.get("SubNamespace")
    target_email: str = spec.get("UserEmail")
    result_code: str = spec.get("ResultCode")

    timestamps = [
        f.create_timestamp("finish execution"),
        f.create_timestamp("start deletion"),
    ]
    # Notify User
    try:
        if TESTING:
            print(result_code)
        else:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Run {subns} has concluded"
            message["From"] = PROGRAM_EMAIL
            message["To"] = target_email
            message.attach(MIMEText(f"Your run has concluded, with code {result_code}"))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context) as server:
                server.login(PROGRAM_EMAIL, PROGRAM_EMAIL_PASSWORD)
                server.sendmail(PROGRAM_EMAIL, [target_email], message.as_string())
    except Exception:
        pass

    # Cleanup
    try:
        print(subprocess.getoutput(DELETE_SUB_NAMESPACE(subns, NAMESPACE)))
        print(subprocess.getoutput(DELETE_START(start_obj)))
        print(subprocess.getoutput(DELETE_FINISH(start_obj)))
        print(subprocess.getoutput(DELETE_PV(f"pv-{subns}")))
    except Exception:
        pass

    # Wait for finishing cleanup
    try:
        flag = True
        while flag:
            if f.cleanup_finished():
                timestamps.append(f.create_timestamp("finish deletion"))
                flag = False
            else:
                time.sleep(1)
    except Exception:
        pass

    # Add timestamps
    f.add_stamps(subns, timestamps)