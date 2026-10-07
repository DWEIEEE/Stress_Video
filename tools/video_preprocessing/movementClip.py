import os
from moviepy import VideoFileClip
import glob
import argparse
import json

S1_move_table = [
    "demi-plié 1ere", "demi-plié 2e", "demi-plié 4e", "Cambré 4e",
    "Tout le tour", "grand plié 4e", "grand-plié 1ere", "penché côté barre",
    "penché en avant 1ere", "penché en avant 4e", "penché extérieur",
    "transition 4e", "transition 5e", "équilibre 1ere"
]

S2_move_table = [
    "pas de gigue releve", "équilibre cheville derrière", "équilibre cheville devant"
]

S1_move_table_en = [
    "Demi-plié 1st",
    "Demi-plié 2nd",
    "Demi-plié 4th",
    "Cambré 4th",
    "Full turn",
    "Grand plié 4th",
    "Grand plié 1st",
    "Side tilt (barre)",
    "Forward tilt 1st",
    "Forward tilt 4th",
    "Outward tilt",
    "Transition 4th",
    "Transition 5th",
    "Balance 1st"
]

S2_move_table_en = [
    "Gigue step",
    "Back ankle balance",
    "Front ankle balance"
]

S3_move_table = [
    "penché en avant",
    "Battement D dev rapide",
    "Battement G der rapide",
    "Battement G dev lent",
    "Battement G dev rapide",
    "battement D dev lent",
    "battement côté lent",
    "battement côté rapide"
]

S3_move_table_en = [
    "Forward tilt",
    "Right front battement fast",
    "Left back battement fast",
    "Left front battement slow",
    "Left front battement fast",
    "Right front battement slow",
    "Side battement slow",
    "Side battement fast"
]

move_translation_en = {
    # S1
    "demi-plié 1ere": "Demi-plié 1st",
    "demi-plié 2e": "Demi-plié 2nd",
    "demi-plié 4e": "Demi-plié 4th",
    "Cambré 4e": "Cambré 4th",
    "Tout le tour": "Full turn",
    "grand plié 4e": "Grand plié 4th",
    "grand-plié 1ere": "Grand plié 1st",
    "penché côté barre": "Side tilt (barre)",
    "penché en avant 1ere": "Forward tilt 1st",
    "penché en avant 4e": "Forward tilt 4th",
    "penché extérieur": "Outward tilt",
    "transition 4e": "Transition 4th",
    "transition 5e": "Transition 5th",
    "équilibre 1ere": "Balance 1st",

    # S2
    "pas de gigue releve": "Gigue step",
    "équilibre cheville derrière": "Back ankle balance",
    "équilibre cheville devant": "Front ankle balance",

    # S3
    "penché en avant": "Forward tilt",
    "Battement D dev rapide": "Right front battement fast",
    "Battement G der rapide": "Left back battement fast",
    "Battement G dev lent": "Left front battement slow",
    "Battement G dev rapide": "Left front battement fast",
    "battement D dev lent": "Right front battement slow",
    "battement côté lent": "Side battement slow",
    "battement côté rapide": "Side battement fast"
}

def main(kwargs):

    data_path = os.path.join(kwargs["path"], kwargs["ex"])
    anno_path = os.path.join(kwargs["annopath"], kwargs["ex"])
    out_path = os.path.join(kwargs["outpath"], kwargs["ex"])

    if not os.path.exists(data_path):
        print(f"The Data Path does not exist ...")
        return

    if not os.path.exists(anno_path):
        print(f"The Anno Path does not exist ...")
        return

    basename = os.path.basename(data_path)
    os.makedirs(out_path, exist_ok=True)

    num = 1

    if kwargs["ex"] == "EX1":
        tab = S1_move_table
        tab_en = S1_move_table_en
    elif kwargs["ex"] == "EX2":
        tab = S2_move_table
        tab_en = S2_move_table_en
    elif kwargs["ex"] == "EX3":
        tab = S3_move_table
        tab_en = S3_move_table_en
    else:
        ValueError("EX error")

    mv_storage = []
    while True:
        print(f"Now 1 : {num}")
        if num == 26:
            num += 1
            continue
        if num == 87:
            num += 1
        if num > 90:
            with open(os.path.join(out_path, "mv_timestamp.json"), "w", encoding="utf-8") as f:
                json.dump(all_persons, f, ensure_ascii=False, indent=4)
            break
        print(f"Now 2 : {num}")
        anno_dir = os.path.join(kwargs["annopath"], kwargs["ex"], f"{basename}-S{str(num)}")
        print(f"anno_dir : {anno_dir}")
        try:
            anno_path = glob.glob(os.path.join(anno_dir, "*.txt"))[0]
            print(f"anno_path : {anno_path}")
        except:
            if not check_exist(anno_dir):
                break
            else:
                print(f"!! S{num} does not have  the annotation file.")
                num += 1
                continue
        print(f"Now 3 : {num}")
        reading_docs, minus = read_file(anno_path, num, tab)
        print(f"{num} : {len(reading_docs)} clips")
        print(f"reading docs : {reading_docs}")

        # Clip the Video
        save_path = os.path.join(out_path, f"{basename}-S{str(num)}")
        os.makedirs(save_path, exist_ok=True)

        for idx, clip_info in enumerate(reading_docs):
            print(f"Dancer {num} : {clip_info['move']} ({idx}/{len(reading_docs)})")
            print(f"info : {clip_info}")
            clip_info['start'] = float(clip_info['start']) - float(minus)
            clip_info['end'] = float(clip_info['end']) - float(minus)
            reading_docs[idx]['start'] = clip_info['start']
            reading_docs[idx]['end'] = clip_info['end']
            print("=> FACE")
            try:
                if check_exist(os.path.join(save_path, f"{basename}-S{str(num)}-face-{clip_info['move']}.mp4")) == False:
                    video_path = os.path.join(data_path, f"{basename}-S{str(num)}", f"{basename}-S{str(num)}-face.mp4")
                    clip = VideoFileClip(video_path)
                    clip = VideoFileClip(video_path).subclipped(clip_info['start'], clip_info['end'])
                    clip.write_videofile(os.path.join(save_path, f"{basename}-S{str(num)}-face-{clip_info['move']}.mp4"), codec="libx264", audio=False)
            except:
                print(f"NO FACE Video or error happened")
            print(f"=> SIDE")
            try:
                if check_exist(os.path.join(save_path, f"{basename}-S{str(num)}-side-{clip_info['move']}.mp4")) == False:
                    video_path = os.path.join(data_path, f"{basename}-S{str(num)}", f"{basename}-S{str(num)}-side.mp4")
                    clip = VideoFileClip(video_path)
                    clip = VideoFileClip(video_path).subclipped(clip_info['start'], clip_info['end'])
                    clip.write_videofile(os.path.join(save_path, f"{basename}-S{str(num)}-side-{clip_info['move']}.mp4"), codec="libx264", audio=False)
            except:
                print(f"NO SIDE Video or error happened")
        
        mv_storage.append(reading_docs)
        num += 1


def read_file(path, mark, tab, key="TAG"):
    out = []
    tmp = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    for ln in lines:
        parts = ln.split("\t")
        first = parts[0].strip()
        move = parts[-1].strip()
        
        if move == key and parts[1] == "S"+str(mark):
            minus = parts[3]

        if first == "execution reelle" and parts[1] == "S"+str(mark) and move in tab:
            move = move_translation_en[move]
            if move in tmp:
                move = move + "_2nd"
            out.append({"num": mark, "move": move, "start": parts[2], "end": parts[3], "long": parts[4]})
            tmp.append(move)
            
    return out, minus


def check_exist(path):
    if os.path.exists(path):
        return True
    return False

if __name__ == "__main__":
    # python movementClip.py --path "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/DanceClip_TAG" --annopath "/srv/storage/stars@storage3.sophia.grid5000.fr/qmerille/qmerille/workspace/dataset/danse" --outpath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MovementClip_TAG"
    
    parser = argparse.ArgumentParser(description="Clip the dancing video Tool")

    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--annopath", type=str, required=True)
    parser.add_argument("--outpath", type=str, required=True)
    parser.add_argument("--ex", type=str, default="EX3")

    args = parser.parse_args()
    kwargs = vars(args)
    main(kwargs)
