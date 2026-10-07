import os
import glob
import argparse
import json
import re
from pprint import pprint
from collections import defaultdict
from moviepy import VideoFileClip

EXCLUDE_MOVES = {
    "conclusion",
    "Conclusion",
    "ERREUR"
    "erreur", "0.007"
}

def normalize_move(name):
    name = name.lower().strip()
    name = (
        name.replace("é", "e")
            .replace("è", "e")
            .replace("ê", "e")
            .replace("à", "a")
            .replace("ç", "c")
    )
    return name

def sum_moves_per_ex(mvbank):
    total = defaultdict(int)

    for person in mvbank:
        for _, moves in person.items():
            for move, count in moves.items():
                norm = normalize_move(move)

                if norm in EXCLUDE_MOVES:
                    continue

                total[norm] += count

    return dict(total)

def extract_number(name):
    match = re.search(r"S(\d+)", name)
    return int(match.group(1)) if match else float("inf")

def check_txtin(path):
    return any(
        fname.endswith(".txt")
        for fname in os.listdir(path)
    )

def extract_subject_id(path):
    match = re.search(r"-S(\d+)", path)
    if match:
        return f"S{match.group(1)}"
    return None

def getjsoname(path):
    for fname in os.listdir(path):
        if fname.endswith(".txt"):
            return fname
    return None


def readjson(path, key, ex):
    move_dict = dict()
    clip_bank = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    for ln in lines:
        parts = ln.split("\t")
        if len(parts) < 5:
            continue
        
        first = parts[0].strip()
        move = parts[-1].strip()

        if move == "TAG" and parts[1] == key:
            minus = float(parts[3])
            continue
        
        if parts[-1] in EXCLUDE_MOVES:
            continue

        if parts[1] == key and first == "execution reelle":
            if move in move_dict: 
                move_dict[move] += 1
            else:
                move_dict[move] = 1
            s = float(parts[2]) - float(minus)
            e = float(parts[3]) - float(minus)
            l = e - s
            clip_bank.append({"name": key, "ex": ex, "num": move_dict[move], "mv": move, "s": s, "e": e, "long": l})

    return {key : move_dict}, clip_bank

def main(kwargs):
    path = kwargs["path"]
    outpath = kwargs["outpath"]
    datapath = kwargs["datapath"]
    exlist = ["EX1", "EX2", "EX3"]
    modeview = 'face'
    bigmvbank = dict()
    bigclipbank = []
    for ex in exlist:
        inpath = os.path.join(path, ex)
        folders = sorted(os.listdir(inpath), key=extract_number)
        count_folder = 0
        mvbank = []
        for folder in folders:
            if folder in ["EX1-S0", "EX2-S0", "EX3-S0"]:
                continue
            infpath = os.path.join(inpath, folder)  
            ans_check_txtin = check_txtin(infpath)      
            if ans_check_txtin == False:
                continue
            else:
                count_folder += 1
            get_json_name = getjsoname(infpath)
            jsonpath = os.path.join(infpath, get_json_name)
            keyname = extract_subject_id(jsonpath)
            outcome, clip_info = readjson(jsonpath, key=keyname, ex=ex)
            mvbank.append(outcome)
            bigclipbank.append(clip_info)
        bigmvbank[ex] = mvbank
        #pprint(mvbank, width=120)
        print(f"[ {ex} ] : {count_folder} folder ")
    
    ex1_sum = sum_moves_per_ex(bigmvbank["EX1"])
    ex2_sum = sum_moves_per_ex(bigmvbank["EX2"])
    ex3_sum = sum_moves_per_ex(bigmvbank["EX3"])
    print(f"\nEX1({len(ex1_sum)}): ", ex1_sum)
    print(f"\nEX2({len(ex2_sum)}): ", ex2_sum)
    print(f"\nEX3({len(ex3_sum)}): ", ex3_sum)
    #pprint(bigclipbank, width=120)
    
    clip_mv_count = dict()
    for bigc in bigclipbank:
        for c in bigc:
            print(f"Doing : {c}")
            tmp = c['mv']
            if tmp not in clip_mv_count:
                clip_mv_count[c['mv']] = 1
                os.makedirs(os.path.join(outpath, c['mv']), exist_ok=True)
            else:
                clip_mv_count[c['mv']] += 1
            
            video_path = os.path.join(
                    datapath, f"{c['ex']}",
                    f"{c['ex']}-{c['name']}",
                    f"{c['ex']}-{c['name']}-{modeview}.mp4"
                )
            if not os.path.exists(video_path):
                continue
            out = os.path.join(
                outpath, c['mv'],
                f"{c['ex']}-{c['name']}-face-{c['mv']}-{c['num']}.mp4"
            )
            if os.path.exists(out):
                print(f"Already has the video : {c['ex']}-{c['name']}-{modeview}.mp4")
                continue

            start = round(c['s'],2)
            end = round(c['e'],2)
            clip = VideoFileClip(video_path)
            duration = clip.duration
            #print(f"duration : {duration}")
            if end > duration:
                end = round(duration, 2)
                print(f"+> Duration ERROR !!!!!!!!!!!!!!!")
            #print(f"{start} , {end}")
            subclip = clip.subclipped(start, end)
            subclip.write_videofile(out, codec="libx264", audio=False)
            subclip.close()
            clip.close()
    pprint(clip_mv_count, width=120)

if __name__ == "__main__":
    # python OrganizeMove.py --path "/srv/storage/stars@storage3.sophia.grid5000.fr/qmerille/qmerille/workspace/dataset/danse" --datapath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/DanceClip_TAG" --outpath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MovementClip_Dataset"

    parser = argparse.ArgumentParser(description="Clip the dancing video Tool")
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--datapath", type=str, required=True)
    parser.add_argument("--outpath", type=str, required=True)
    args = parser.parse_args()
    kwargs = vars(args)
    main(kwargs)
