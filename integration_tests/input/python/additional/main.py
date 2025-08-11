from aas_core import jsonization, xmlization
import sys
import os
import json

if __name__ == "__main__":
    data_dir = sys.argv[1]
    for file in os.listdir(data_dir):
        p = os.path.join(data_dir, file)
        print(f"Checking {p}")
        if file.endswith("json"):
            with open(p) as fd:
                data = json.load(fd)
            jsonization.root_from_jsonable(data)
        else:
            with open(p) as fd:
                xmlization.root_from_stream(fd)
