import pickle
import subprocess


def run_report(name, data_blob):
    subprocess.call("generate_report " + name, shell=True)
    config = pickle.loads(data_blob)
    return config["output"]
