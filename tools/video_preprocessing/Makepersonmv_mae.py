import os
import argparse 
import re
import cv2

def check_exist(path):
    return os.path.isfile(path)

def makeVideoClip(person_crop_dir, name, save_path):
    file_list = [f"{name}.jpg"]
    file_num = 2
    if check_exist(os.path.join(person_crop_dir, f"{name}{file_num}.jpg")):
        print("True")
    else:
        print("False")
    while check_exist(os.path.join(person_crop_dir, f"{name}{file_num}.jpg")):
        file_list.append(f"{name}{file_num}.jpg")
        file_num += 1
    
    #add
    output_video_path = os.path.join(save_path, f"PersonClip_{name}.mp4")
    if check_exist(output_video_path):
        return
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(
        output_video_path,
        fourcc,
        30,
        (224, 224)
    )

    for rf in file_list:
        img = cv2.imread(os.path.join(person_crop_dir, rf))
        img = cv2.resize(img, (224, 224))
        writer.write(img)
    writer.release()

def main(kwargs):
    root_path = kwargs["path"]

    print(f"Searching folders in: {root_path}")
    print("-" * 50)

    count = 0

    # only search first-level folders
    for name in sorted(os.listdir(root_path)):
        folder_path = os.path.join(root_path, name)
        person_crop_dir = os.path.join(folder_path, "crops", "person")
        target_file = f"{name}.jpg"
        target_path = os.path.join(person_crop_dir, target_file)

        if os.path.isfile(target_path):
            print(f"  [FOUND] {target_file}")
            count += 1
            makeVideoClip(person_crop_dir=person_crop_dir,
                name=name, save_path=folder_path)
        else:
            print(f"  [MISSING] {target_file}")

    print("-" * 50)
    print(f"total : {count}")
    print("Done.")

        
if __name__ == "__main__":
    # python Makepersonmv_mae.py --path "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MovementClip_Dataset_Yolo/préparation en musique"

    parser = argparse.ArgumentParser(description="Clip the dancing video Tool")

    parser.add_argument("--path", type=str, required=True)

    args = parser.parse_args()
    kwargs = vars(args)
    main(kwargs)
