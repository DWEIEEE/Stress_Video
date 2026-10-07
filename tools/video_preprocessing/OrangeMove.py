import os
import glob
import argparse
import json

def main(kwargs):
    path = kwargs["path"]
    exlist = ["EX1", "EX2", "EX3"]
    
    for ex in exlist:
        inpath = os.path.join(path, ex)
        print(os.listdir(inpath))



if __name__ == "__main__":
    # python OrganizeMove.py --path "/srv/storage/stars@storage3.sophia.grid5000.fr/qmerille/qmerille/workspace/dataset/danse"

    parser = argparse.ArgumentParser(description="Clip the dancing video Tool")
    parser.add_argument("--path", type=str, required=True)
    args = parser.parse_args()
    kwargs = vars(args)
    main(kwargs)
