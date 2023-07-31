import time
import smtplib
import ssl
import subprocess
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread
# from dotenv import load_dotenv

# sys.path.append("../")
# Custom code
import creator as c
import functions as f


# load_dotenv()

NAMESPACE = "serverless-graphs"
DELETE_SUB_NAMESPACE = lambda child, parent: f"kubectl delete subns {child} -n {parent}"
DELETE_START = lambda obj: f"kubectl delete start {obj} -n {NAMESPACE}"
DELETE_FINISH = lambda obj: f"kubectl delete finish {obj} -n {NAMESPACE}"
DELETE_PV = lambda pv: f"kubectl delete pv {pv}"

TESTING = True

SMTP_SERVER = "smtp.gmail.com"
PROGRAM_EMAIL = os.getenv("EMAIL")
PROGRAM_EMAIL_PASSWORD = os.getenv("PASSWORD")

def get_crs(type: str = "start"):
    start_crs_text = subprocess.getoutput(f"kubectl get {type} -n {NAMESPACE}").split("\n")[1:]
    return [i.split(" ")[0] for i in start_crs_text]

def get_spec(object: str, type: str = "start"):
    descirbed = subprocess.getoutput(f"kubectl describe {type} {object} -n {NAMESPACE}")
    spec = descirbed.split("Spec:")[1]
    spec_dict = {}
    for line in spec.split("\n"):
        try:
            k, v = line.split(":")
            k, v = k.strip(), v.strip()
            spec_dict[k] = v
        except:
            pass
    return spec_dict

def creating(start_cr, counter):
    timestamps = [f.create_timestamp("start creation")]

    spec = get_spec(start_cr)

    # Setup generics
    crd_name: str = start_cr
    tenant: str = spec["Tenant"].lower()
    user: str = spec["User"].lower()
    user_email: str = spec["User Email"]

    # Setup run specifics
    nrWorkers: int = spec["Nr Workers"]
    run_id: int = counter
    file: str = f"mount.{spec['Graph Location']}"
    execution_name: str = f"{tenant}-{user}-{run_id}"

    # Create all objects
    c.via_file(
        NAMESPACE,
        execution_name,
        nrWorkers,
        crd_name,
        file,
        user_email,
        str(spec["Tenant"]),
        counter,
    )
    
    timestamps.append(f.create_timestamp("finish creation"))
    timestamps.append(f.create_timestamp("start execution"))
    f.add_stamps(execution_name, timestamps, header=True)

def clearing(finish_cr):
    timestamps = [
        f.create_timestamp("finish execution"),
        f.create_timestamp("start deletion"),
    ]

    spec = get_spec(finish_cr, "finish")

    start_obj: str = spec["Start"]
    subns: str = spec["Sub Namespace"]
    target_email: str = spec["User Email"]
    result_code: str = spec["Result Code"]
    
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
        subprocess.run(DELETE_SUB_NAMESPACE(subns, NAMESPACE), shell=True)
        subprocess.run(DELETE_START(start_obj), shell=True)
        subprocess.run(DELETE_FINISH(start_obj), shell=True)
        subprocess.run(DELETE_PV(f"pv-{subns}"), shell=True)
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

    f.add_stamps(subns, timestamps)

    # Clean lists
    global known_start_crs
    global known_finish_crs

    known_start_crs.remove(start_obj)
    known_finish_crs.remove(start_obj)

    with open('run-info.txt') as file:
        lines = file.readlines()

    lines[1] = "True\n"

    with open('run-info.txt', 'w') as file:
            file.writelines(lines)

#   _                                     _       _     _           
#  | |                                   (_)     | |   | |          
#  | | ___   ___  _ __   __   ____ _ _ __ _  __ _| |__ | | ___  ___ 
#  | |/ _ \ / _ \| '_ \  \ \ / / _` | '__| |/ _` | '_ \| |/ _ \/ __|
#  | | (_) | (_) | |_) |  \ V / (_| | |  | | (_| | |_) | |  __/\__ \
#  |_|\___/ \___/| .__/    \_/ \__,_|_|  |_|\__,_|_.__/|_|\___||___/
#                | |                                                
#                |_|                                                

known_start_crs = []
known_finish_crs = []
counter = 0

print("running...")
def creating_loop():
    global known_start_crs
    global known_finish_crs
    global counter

    while True:
        active_start_crs = get_crs()

        for start_cr in active_start_crs:
            # This start_cr is already known and is not intressting
            if start_cr in known_start_crs or start_cr in known_finish_crs:
                continue
            # New start_cr
            else:
                print("creating")
                known_start_crs.append(start_cr)
                thread = Thread(target=creating, args=(start_cr,counter))
                thread.start()
                
                # Update counter
                counter = counter + 1 if counter < 100 else 0
        time.sleep(1)

def clearning_loop():
    while True:
        active_finish_crs = get_crs("finish")

        for finish_cr in active_finish_crs:
            # This finish_cr is already known and is not intressting
            if finish_cr in known_finish_crs:
                continue
            # New finish_cr
            else:
                print(f"cleaning, {finish_cr}")
                known_finish_crs.append(finish_cr)
                thread = Thread(target=clearing, args=(finish_cr,))
                thread.start()
        time.sleep(1)


if __name__ == '__main__':
    clean = Thread(target=clearning_loop)
    clear = Thread(target=creating_loop)
    clean.start()
    clear.start()