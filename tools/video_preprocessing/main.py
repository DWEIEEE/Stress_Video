from moviepy import VideoFileClip
import argparse
import glob
import os

def check_video_files(folder):
    video_files = []

    for ext in ["*.mp4", "*.mov", "*.MP4", "*.MOV"]:
        video_files.extend(glob.glob(os.path.join(folder, ext)))

    video_names = [os.path.basename(v) for v in video_files]

    if len(video_files) >= 2:
        print(f"   Video files ({len(video_files)}):")
        for name in video_names:
            print(f"      - {name}")
    else:
        print(f"!! {os.path.basename(folder)} has less than 2 video files.")
        print(f"   Found video files ({len(video_files)}):")
        for name in video_names:
            print(f"      - {name}")

    return video_files

def main(kwargs):

    data_path = kwargs["path"]
    out_path = kwargs["outpath"]
    start_word = kwargs["start"]
    end_word = kwargs["end"]
    if not os.path.exists(data_path):
        print(f"The Path does not exist ...")
        return

    basename = os.path.basename(data_path)
    os.makedirs(out_path, exist_ok=True)

    if kwargs["assign"] != None:
        num = kwargs["assign"]
    else:
        num = 85

    while True:
        if num == 87:
            num += 1
            continue
        if num == 26:
            num += 1
            continue
        anno_dir = os.path.join(data_path, f"{basename}-S{str(num)}")
        try:
            anno_path = glob.glob(os.path.join(anno_dir, "*.txt"))[0] 
        except:
            if not check_exist(anno_dir):
                break
            else:
                print(f"!! S{num} does not have  the annotation file.")
                num += 1
                continue
        video_files = check_video_files(anno_dir)
        if kwargs["assign"] == None:
            stime, etime = read_file(anno_path, start_word, end_word, num)
        else:
            stime = float(start_word)
            etime = float(end_word)

        if stime == None:
            print(f"!! S{num} does not have the {start_word} in the annotation file.")
            num += 1
            continue
        if etime == None:
            print(f"!! S{num} does not have the {end_word} in the annotation file.")
            num += 1
            continue
        print(f"[S{num}] time : {stime} - {etime} ({float(etime)-float(stime):.2f})")
        
        if kwargs["display"]:
            num += 1
            continue
        
        # Clip the Video
        save_path = os.path.join(out_path, f"{basename}-S{str(num)}")
        os.makedirs(save_path, exist_ok=True)
        try:
            #video_path = os.path.join(data_path, f"{basename}-S{str(num)}", f"{basename}-S{str(num)}.mp4")
            video_path = os.path.join(data_path, f"{basename}-S{str(num)}", f"{basename}-S{str(num)}-diago.mov")    
            clip = VideoFileClip(video_path)
            if float(etime) > float(clip.duration):
                etime = float(clip.duration)
            clip = VideoFileClip(video_path).subclipped(stime, etime)
            clip.write_videofile(os.path.join(save_path, f"{basename}-S{str(num)}-side.mp4"), codec="libx264", audio=False)
        except:
            video_path = os.path.join(data_path, f"{basename}-S{str(num)}", f"{basename}-S{str(num)}-face.mp4")
            clip = VideoFileClip(video_path)
            if float(etime) > float(clip.duration):
                etime = float(clip.duration)
            clip = VideoFileClip(video_path).subclipped(stime, etime)
            clip.write_videofile(os.path.join(save_path, f"{basename}-S{str(num)}-face.mp4"), codec="libx264", audio=False)
        
        num += 1
        if kwargs["assign"] != None:
            break

def read_file(path, sw, ew, mark):
    st, et = None, None
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    for ln in lines:
        parts = ln.split("\t")
        desc = parts[-1].strip()
        
        if desc == sw and parts[1] == "S"+str(mark):
            st = parts[3]#[2]

        if desc == ew and parts[1] == "S"+str(mark):
            et = parts[3]
    
    return st, et

def check_exist(path):
    if os.path.exists(path):
        return True
    return False

if __name__ == "__main__":
    # python main.py --path "/srv/storage/stars@storage3.sophia.grid5000.fr/qmerille/qmerille/workspace/dataset/danse/EX3" --outpath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/DanceClip_TAG/EX3"
    
    parser = argparse.ArgumentParser(description="Clip the dancing video Tool")

    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--outpath", type=str, required=True)
    parser.add_argument("--start", type=str, default="TAG")#"préparation")
    parser.add_argument("--end", type=str, default="conclusion")#Conclusion for EX1
    parser.add_argument("--assign", type=int, default=None)
    parser.add_argument("--display", type=bool, default=False)

    args = parser.parse_args()
    kwargs = vars(args)
    main(kwargs)
