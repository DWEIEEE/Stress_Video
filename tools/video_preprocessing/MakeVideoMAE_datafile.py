import os
import argparse
import pandas as pd
import random
from collections import Counter, defaultdict

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
    mv = kwargs["mv"]

    os.makedirs(output_dir, exist_ok=True)

    # -----------------------------------------------------
    # load labels
    # -----------------------------------------------------
    df = pd.read_excel(label_path)
    column_name = "Stress ressenti frappé (EX2)"
    stress_values = df[column_name]
    print(f"{type(stress_values)}before : ", stress_values)
    stress_values, TARGET_DISTRIBUTION = thre(stress_values,3)
    stress_values = stress_values.reset_index(drop=True)
    print("after : ", stress_values)
    # -----------------------------------------------------
    # collect samples
    # -----------------------------------------------------
    folder_list = sorted(
        os.listdir(data_path),
        key=lambda x: int(x.split("-S")[-1])
    )

    samples = []
    all_labels = []

    for folder in folder_list:
        num = int(folder.split("-S")[-1])  # S1 -> 1
        
        wmv = mv.replace(" ", "")
        mp4_path = os.path.join(
            data_path,
            folder,
            f"PersonClip_{folder}-{wmv}.mp4"
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

        samples.append(f"{mp4_path} {label}")
        all_labels.append(label)

    print(f"\nTotal valid samples: {len(samples)}")

    # -----------------------------------------------------
    # overall distribution
    # -----------------------------------------------------
    print("\nOverall label distribution:")
    overall_counter = Counter(all_labels)
    for k in range(10):
        print(f"  class {k}: {overall_counter.get(k, 0)}")

    # -----------------------------------------------------
    # stratified split with fixed targets
    # -----------------------------------------------------
    by_class = defaultdict(list)
    for s in samples:
        label = int(s.split()[-1])
        by_class[label].append(s)

    train_samples, val_samples, test_samples = [], [], []

    random.seed(42)

    for cls in sorted(by_class.keys()):
        cls_samples = by_class[cls]
        random.shuffle(cls_samples)
        
        n_val = TARGET_DISTRIBUTION.get(cls, 0)
        n_test = TARGET_DISTRIBUTION.get(cls, 0)

        if n_val + n_test > len(cls_samples):
            raise ValueError(
                f"Class {cls}: need {n_val+n_test}, "
                f"but only {len(cls_samples)} available"
            )
        
        val_samples.extend(cls_samples[:n_val])
        test_samples.extend(cls_samples[n_val:n_val + n_test])
        train_samples.extend(cls_samples[n_val + n_test:])

    # -----------------------------------------------------
    # sanity check distributions
    # -----------------------------------------------------
    def count_labels(sample_list):
        return Counter(int(s.split()[-1]) for s in sample_list)

    print("\nTRAIN label distribution:")
    for k in range(10):
        print(f"  class {k}: {count_labels(train_samples).get(k, 0)}")

    print("\nVAL label distribution:")
    for k in range(10):
        print(f"  class {k}: {count_labels(val_samples).get(k, 0)}")

    print("\nTEST label distribution:")
    for k in range(10):
        print(f"  class {k}: {count_labels(test_samples).get(k, 0)}")

    # -----------------------------------------------------
    # write csv
    # -----------------------------------------------------
    def write_csv(name, data):
        path = os.path.join(output_dir, name)
        with open(path, "w") as f:
            for line in data:
                #line = line.replace(" ", "")
                f.write(line + "\n")
        print(f"Written {path} ({len(data)} samples)")

    write_csv("train.csv", train_samples)
    write_csv("val.csv", val_samples)
    write_csv("test.csv", test_samples)

    print("\nDone.")

# =========================================================
if __name__ == "__main__":

#python MakeVideoMAE_datafile.py --datapath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/YoloPose_UNIK_MoveClip_TAG/EX2" --mv "face-Front ankle balance" --labelpath "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/DanceClip_TAG/stress_label_84.xlsx" --outdir "/srv/storage/stars@storage3.sophia.grid5000.fr/dlai/Dataset/VideoMAE_datafile/3class"

    parser = argparse.ArgumentParser("Prepare VideoMAE dataset")

    parser.add_argument("--datapath", type=str, required=True)
    parser.add_argument("--labelpath", type=str, required=True)
    parser.add_argument("--mv", type=str, required=True)
    parser.add_argument("--outdir", type=str, required=True)

    args = parser.parse_args()
    main(vars(args))
