import subprocess
from csv import writer
from datetime import date, datetime

NAMESPACE = "serverless-graphs"
NO_RESOURCE = f"No resources found in {NAMESPACE} namespace."
HEADER = ["Action", "Date", "Time"]
FOLDER = "[ADD FOLDER]"

def cleanup_finished() -> bool:
    return subprocess.getoutput(f"kubectl get all -n {NAMESPACE}") == NO_RESOURCE


def create_timestamp(action: str) -> list:
    _, __ = str(datetime.now()).split(" ")
    return [action, _, __]


def add_stamps(
    execution_name: str, stamps: list[list[str, str, str]], header: bool = False
):
    save_file_template = (
        f"{FOLDER}/{execution_name}-{date.today()}.csv"
    )
    operation = "w" if header else "a"
    with open(save_file_template, operation) as outfile:
        writer_object = writer(outfile)
        if header:
            writer_object.writerow(HEADER)
        else:
            writer_object.writerow([])
        writer_object.writerows(stamps)
        outfile.close()
