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
    "équilibre cheville devant": "Front ankle balance"
}


def main(kwargs):
    data_path = os.path.join(kwargs["path"], kwargs["ex"])
    anno_root = os.path.join(kwargs["annopath"], kwargs["ex"])
    out_path = os.path.join(kwargs["outpath"], kwargs["ex"])

    if not os.path.exists(data_path):
        print("The Data Path does not exist ...")
        return

    if not os.path.exists(anno_root):
        print("The Anno Path does not exist ...")
        return

    basename = os.path.basename(data_path.rstrip("/"))
    os.makedirs(out_path, exist_ok=True)

    if kwargs["ex"] == "EX1":
        tab = S1_move_table
        tab_en = S1_move_table_en  # currently unused but kept
    elif kwargs["ex"] == "EX2":
        tab = S2_move_table
        tab_en = S2_move_table_en  # currently unused but kept
    else:
        raise ValueError("EX error: should be EX1 or EX2")

    mv_storage = []
    num = 1

    while True:
        if num == 26:
            num += 1
            continue

        if num > 47:
            # save all timestamps and exit
            json_path = os.path.join(out_path, "mv_timestamp.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(mv_storage, f, ensure_ascii=False, indent=4)
            print(f"Saved json: {json_path}")
            break

        anno_dir = os.path.join(anno_root, f"{basename}-S{num}")
        try:
            anno_file = glob.glob(os.path.join(anno_dir, "*.txt"))[0]
        except IndexError:
            if not check_exist(anno_dir):
                # no more S<num> folders, stop
                break
            else:
                print(f"!! S{num} does not have the annotation file.")
                num += 1
                continue

        reading_docs, minus = read_file(anno_file, num, tab)
        if not reading_docs:
            print(f"{num}: no valid clips found, skip.")
            num += 1
            continue

        print(f"{num} : {len(reading_docs)} clips")
        print(f"reading docs : {reading_docs}")

        # Clip the Video
        save_path = os.path.join(out_path, f"{basename}-S{num}")
        os.makedirs(save_path, exist_ok=True)

        for idx, clip_info in enumerate(reading_docs):
            print(f"Dancer S{num} : {clip_info['move']} ({idx+1}/{len(reading_docs)})")
            print(f"minus : {minus}")
            start = float(clip_info["start"]) - float(minus)
            end = float(clip_info["end"]) - float(minus)
            clip_info["start"] = start
            clip_info["end"] = end
            print(f"info : {clip_info}")
            print(f"minus : {minus}")
            reading_docs[idx] = clip_info

            # FACE
            print("=> FACE")
            face_video_path = os.path.join(
                data_path,
                f"{basename}-S{num}",
                f"{basename}-S{num}-face.mp4"
            )
            if os.path.exists(face_video_path):
                try:
                    if check_exist(os.path.join(
                        save_path,
                        f"{basename}-S{num}-face-{clip_info['move']}.mp4"
                    )) == False:
                        clip = VideoFileClip(face_video_path).subclipped(start, end)
                        out_face = os.path.join(
                            save_path,
                            f"{basename}-S{num}-face-{clip_info['move']}.mp4"
                        )
                        clip.write_videofile(out_face, codec="libx264", audio=False)
                except Exception as e:
                    print(f"Error writing FACE clip for S{num}, move {clip_info['move']}: {e}")
            else:
                print(f"[WARN] FACE video not found: {face_video_path}")

            # SIDE
            print("=> SIDE")
            side_video_path = os.path.join(
                data_path,
                f"{basename}-S{num}",
                f"{basename}-S{num}-side.mp4"
            )
            if os.path.exists(side_video_path):
                try:
                    if check_exist(os.path.join(
                        save_path,
                        f"{basename}-S{num}-side-{clip_info['move']}.mp4"
                    )) == False:
                        clip = VideoFileClip(side_video_path).subclipped(start, end)
                        out_side = os.path.join(
                            save_path,
                            f"{basename}-S{num}-side-{clip_info['move']}.mp4"
                        )
                        clip.write_videofile(out_side, codec="libx264", audio=False)
                except Exception as e:
                    print(f"Error writing SIDE clip for S{num}, move {clip_info['move']}: {e}")
            else:
                print(f"[WARN] SIDE video not found: {side_video_path}")

        mv_storage.append(reading_docs)
        num += 1


def read_file(path, mark, tab, key="TAG"):
    out = []
    tmp = []
    minus = 0.0

    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    for ln in lines:
        parts = ln.split("\t")
        if len(parts) < 5:
            continue

        first = parts[0].strip()
        move = parts[-1].strip()

        # TAG line: define minus (time offset)
        if move == key and parts[1] == f"S{mark}":
            minus = float(parts[3])
            continue

        # execution real clips
        if first == "execution reelle" and parts[1] == f"S{mark}" and move in tab:
            translated = move_translation_en.get(move, move)
            if translated in tmp:
                translated = translated + "_2nd"
            out.append({
                "num": mark,
                "move": translated,
                "start": parts[2],
                "end": parts[3],
                "long": parts[4]
            })
            tmp.append(translated)

    return out, minus


def check_exist(path):
    return os.path.exists(path)


if __name__ == "__main__":
    # Example:
    # python try.py --path "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/DanceClip_TAG" \
    #              --annopath "/srv/storage/stars@storage3.sophia.grid5000.fr/qmerille/qmerille/workspace/dataset/danse" \
    #              --outpath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MovementClip_TAG" \
    #              --ex EX1

    parser = argparse.ArgumentParser(description="Clip the dancing video Tool")

    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--annopath", type=str, required=True)
    parser.add_argument("--outpath", type=str, required=True)
    parser.add_argument("--ex", type=str, default="EX1")

    args = parser.parse_args()
    kwargs = vars(args)
    main(kwargs)
