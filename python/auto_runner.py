import time
import subprocess

REPITIONS = 10
SETTINGS = ["sp-kgs"]#, "sp-wiki", "pr-kgs", "sp-kgs"]#, "sp-kgs", "pr-kgs", "tc-wiki", "tc-kgs"]

busy = True
_ = 0

print("running...")
while busy:
    with open('run-info.txt') as f:
        lines = f.readlines()

    iteration = int(lines[0].strip())
    idle = True if lines[1].strip() == "True" else False
    algorithm = lines[2].replace("\n","")

    if idle:
        if any(["tenant" in __ for __ in [_.split(" ", 1)[0] for _ in str(subprocess.getoutput("kubectl get ns")).split("\n")]]):
            time.sleep(15)
            continue
        else:
            if iteration == (REPITIONS - 1):
                iteration = 0
                if algorithm == "none":
                    algorithm = SETTINGS[0]
                else:
                    current_algorithm_index = SETTINGS.index(algorithm)
                    if current_algorithm_index == len(SETTINGS):
                        busy = False
                    else:
                        algorithm = SETTINGS[current_algorithm_index+ 1]

                idle = "False"
            else:
                iteration = iteration + 1
                idle = "False"

            with open('run-info.txt', 'w') as f:
                f.writelines(line + "\n"for line in [str(iteration), idle, algorithm])

            if busy:
                subprocess.run(f"kubectl apply -f yamls/{algorithm}-a.yaml", shell=True)
                time.sleep(10)
                subprocess.run(f"kubectl apply -f yamls/{algorithm}-b.yaml", shell=True)
    time.sleep(30)
