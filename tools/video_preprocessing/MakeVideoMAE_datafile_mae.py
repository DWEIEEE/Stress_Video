import os
import argparse
import pandas as pd
import random
from collections import Counter, defaultdict
import re
import csv
import numpy as np

# =========================================================
# target distribution for VAL / TEST
# =========================================================
TARGET_DISTRIBUTION_10 = {
    0: 0,
    1: 1,
    2: 2,
    3: 2,
    4: 2,
    5: 1,
    6: 1,
    7: 0,
    8: 0,
    9: 0,
}
TARGET_DISTRIBUTION_3 = {
    0: 3,
    1: 3,
    2: 3,
}
TARGET_DISTRIBUTION_2 = {
    0: 4,
    1: 4,
}
EX1_MV_list = [
    "préparation en musique",
    "demi-plié 1ere",
    "grand-plié 1ere",
    "penché en avant 1ere",
    "équilibre 1ere",
    "demi-plié 2e",
    "grand-plié 2e",
    "transition 2e",
    "penché côté barre",
    "penché extérieur",
    "demi-plié 4e",
    "grand plié 4e",
    "penché en avant 4e",
    "Cambré 4e",
    "transition 4e",
    "Demi-plié 5e",
    "Grand-plié 5e",
    "transition 5e",
    "Tout le tour",
    "Equilibre",
    "Etiré de bras"]
EX2_MV_list = [
    "préparation",
    "frappé simple devant",
    "frappé double devant",
    "frappé simple cote",
    "frappé double cote",
    "frappe simple derriere",
    "frappe double derriere",
    "pas de gigue releve",
    "3 ronds simples seconde",
    "battu à la cheville",
    "équilibre cheville devant",
    "équilibre cheville derrière"
]
EX3_MV_list = [
    "preparation",
    "Battement G dev rapide",
    "Battement G dev lent",
    "Battement D dev rapide",
    "battement D dev lent",
    "Battement G der rapide",
    "Battement G der lent",
    "Battement D der rapide",
    "Battement D der lent",
    "battement cote rapide",
    "battement cote lent",
    "penche en avant",
    "penche en arriere"
]
# =========================================================

def thre(stress_series, splits):
    if splits == 3:
        TARGET_DISTRIBUTION = TARGET_DISTRIBUTION_3
        class_map = {
            0: 0, 1: 0, 2: 0,
            3: 1, 4: 1,
            5: 2, 6: 2, 7: 2, 8: 2, 9: 2
        }
    elif splits == 2:
        TARGET_DISTRIBUTION = TARGET_DISTRIBUTION_2
        class_map = {
            0: 0, 1: 0, 2: 0, 3: 0,
            4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1
        }
    else:
        return stress_series, TARGET_DISTRIBUTION_10

    # 關鍵：轉 int + map
    stress_series = stress_series.dropna()
    
    return stress_series.astype(int).map(class_map), TARGET_DISTRIBUTION

def main(kwargs):
    label_path = kwargs["labelpath"]
    data_path = kwargs["datapath"]
    output_dir = kwargs["outdir"]
    num_c = kwargs["num_c"]
    ratio = kwargs["ratio"]

    os.makedirs(output_dir, exist_ok=True)

    # -----------------------------------------------------
    # load labels
    # -----------------------------------------------------
    df = pd.read_excel(label_path)
    #column_name = "Stress ressenti frappé (EX2)"
    #stress_values = df[column_name]
    #print(f"{type(stress_values)}before : ", stress_values)
    column_list = ["Genre", "Amateur/Pro/Pré", "TAS-20", "Stress Cohen", "STAI-Y trait"]
    base_mv = os.path.basename(data_path)
    print(f"base_mv name : {base_mv}")
    if base_mv in EX1_MV_list:
        stress_values = df["Stress ressenti plié (EX1)"]
        column_list.append("stress perçu EX1 juge 1")
        column_list.append("Exécution EX1 juge 1")
        ex = "EX1"
    elif base_mv in EX2_MV_list:
        stress_values = df["Stress ressenti frappé (EX2)"]
        column_list.append("stress perçu EX2 juge 1")
        column_list.append("Exécution EX2 juge 1")
        ex = "EX2"
    elif base_mv in EX3_MV_list:
        stress_values = df["Stress ressenti battement (EX3)"]
        column_list.append("stress perçu EX3 juge 1")
        column_list.append("Exécution EX3 juge 1")
        ex = "EX3"
    else:
        print(f"MV ERROR")
        return
    stress_values, TARGET_DISTRIBUTION = thre(stress_values,num_c)
    stress_values = stress_values.reset_index(drop=True)
    print("after : ", stress_values)
    
    extra_df = df[column_list].reset_index(drop=True)
    # -----------------------------------------------------
    # collect samples
    # -----------------------------------------------------
    folder_list = sorted(
        os.listdir(data_path),
        key=lambda x: int(re.search(r"-S(\d+)", x).group(1))
    )

    samples = []
    all_labels = []

    for folder in folder_list:
        num = int(re.search(r"-S(\d+)", folder).group(1))
        
        mp4_path = os.path.join(
            data_path,
            folder,
            f"PersonClip_{folder}.mp4"
        )

        if not os.path.exists(mp4_path):
            print(f"[Missing] {mp4_path}")
            continue

        # ✅ correct indexing (VERY IMPORTANT)
        label = stress_values[num]

        if pd.isna(label):
            print(f"[Skip NaN] {folder}")
            continue

        label = int(label)

        extra_values = extra_df.iloc[num].tolist()
        extra_values = ["NA" if pd.isna(v) else str(v) for v in extra_values]
        #line = ",".join([mp4_path, str(label)] + extra_values)        
        #samples.append(line)
        samples.append({
            "path": mp4_path,
            "label": label,
            "extra": extra_values
        })   

    print(f"\nTotal valid samples: {len(samples)}")

    # -----------------------------------------------------
    # overall distribution
    # -----------------------------------------------------
    #for s in samples:
        #split_info = s.split(",")
        #print(f"split : {split_info }")

    def random_split(samples, train_ratio=0.8, val_ratio=0.1, seed=None):
        assert train_ratio + val_ratio < 1.0

        if seed is not None:
            random.seed(seed)

        samples = samples.copy()
        random.shuffle(samples)

        n = len(samples)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        train = samples[:n_train]
        val = samples[n_train:n_train + n_val]
        test = samples[n_train + n_val:]

        return train, val, test

    tr = 1 - (2 * ratio)
    train_samples, val_samples, test_samples = random_split(samples, train_ratio=tr, val_ratio=ratio)

    train_labels = np.array([s["label"] for s in train_samples], dtype=int)

    sr_min = train_labels.min()
    sr_max = train_labels.max()

    sr_range = sr_max - sr_min if sr_max != sr_min else 1.0
    def normalize_sr(samples):
        for s in samples:
            s["label"] = (float(s["label"]) - sr_min) / sr_range

    normalize_sr(train_samples)
    normalize_sr(val_samples)
    normalize_sr(test_samples)


    # add
    def extras_to_array(samples):
        return np.array([
                [v if v != "NA" else np.nan for v in s["extra"]]
                for s in samples
            ])

    train_extra = extras_to_array(train_samples)
    val_extra = extras_to_array(val_samples)
    test_extra = extras_to_array(test_samples)
    train_num = np.array([
        [pd.to_numeric(v, errors="coerce") for v in row[2:]]
        for row in train_extra
    ], dtype=float)
    mins = np.nanmin(train_num, axis=0)
    maxs = np.nanmax(train_num, axis=0)

    # 避免除以 0
    ranges = np.where(maxs - mins == 0, 1, maxs - mins)

    # normalization
    for idx, s in enumerate(train_extra):
        for i in range(5):
            train_extra[idx, i+2] = float((float(s[i+2]) - mins[i]) / ranges[i])
    for idx, s in enumerate(val_extra):
        for i in range(5):
            val_extra[idx, i+2] = float((float(s[i+2]) - mins[i]) / ranges[i])
    for idx, s in enumerate(test_extra):
        for i in range(5):
            test_extra[idx, i+2] = float((float(s[i+2]) - mins[i]) / ranges[i])   
    # -----------------------------------------------------
    # write csv
    # -----------------------------------------------------
    def write_csv(name, data, extra):
        header = [
            "path",
            "sr_stress",
            "gender",
            "pro",
            "tas20",
            "cohen",
            "staiy",
            "jg_stress",
            "wellperform",
        ]
        path = os.path.join(output_dir, name)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for i, s in enumerate(data):
                row = [s["path"], s["label"]] + list(extra[i])
                writer.writerow(row)
              
        print(f"Written {path} ({len(data)} samples)")

    write_csv("train.csv", train_samples, train_extra)
    write_csv("val.csv", val_samples, val_extra)
    write_csv("test.csv", test_samples, test_extra)

    print("\nDone.")

# =========================================================
if __name__ == "__main__":

#python MakeVideoMAE_datafile_mae.py --datapath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/MovementClip_Dataset_Yolo/préparation en musique" --labelpath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/DanceClip_TAG/stress_label_84.xlsx" --outdir "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/VideoMAE_datafile_v2/préparation_en_musique_c1"

    parser = argparse.ArgumentParser("Prepare VideoMAE dataset")

    parser.add_argument("--datapath", type=str, required=True)
    parser.add_argument("--labelpath", type=str, required=True)
    parser.add_argument("--num_c", type=int, default=10)
    parser.add_argument("--outdir", type=str, required=True)
    parser.add_argument("--ratio", type=float, default=0.15)

    args = parser.parse_args()
    main(vars(args))
