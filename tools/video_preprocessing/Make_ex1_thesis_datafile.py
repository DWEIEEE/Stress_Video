import argparse
import csv
import os
import random
import re
from collections import Counter, defaultdict

import cv2
import pandas as pd


LABEL_COLUMNS = {
    "EX1": [
        "Stress ressenti plié (EX1)",
        "Stress ressenti plie (EX1)",
    ],
    "EX2": [
        "Stress ressenti frappé (EX2)",
        "Stress ressenti frappe (EX2)",
    ],
    "EX3": [
        "Stress ressenti battement (EX3)",
    ],
}

MOVEMENT_FOLDER_TO_ITEM = {
    "Demi-plié_1st": "Demi-plié 1st",
    "Demi-plié_2nd": "Demi-plié 2nd",
    "Demi-plié_4th": "Demi-plié 4th",
    "Cambré_4th": "Cambré 4th",
    "Full_turn": "Full turn",
    "Grand_plié_1st": "Grand plié 1st",
    "Grand_plié_4th": "Grand plié 4th",
    "Forward_tilt_1st": "Forward tilt 1st",
    "Forward_tilt_4th": "Forward tilt 4th",
    "Outward_tilt": "Outward tilt",
    "Transition_4th": "Transition 4th",
    "Transition_5th": "Transition 5th",
    "Balance_1st": "Balance 1st",
    "Side_tilt_(barre)": "Side tilt (barre)",
    "Gigue_step": "Gigue step",
    "Back_ankle_balance": "Back ankle balance",
    "Front_ankle_balance": "Front ankle balance",
    "Forward_tilt": "Forward tilt",
    "Right_front_battement_fast": "Right front battement fast",
    "Left_back_battement_fast": "Left back battement fast",
    "Left_front_battement_slow": "Left front battement slow",
    "Left_front_battement_fast": "Left front battement fast",
    "Right_front_battement_slow": "Right front battement slow",
    "Side_battement_slow": "Side battement slow",
    "Side_battement_fast": "Side battement fast",
}

CLASS_NAMES = {
    2: {0: "Low stress (0-3)", 1: "High stress (4-9)"},
    3: {
        0: "Low stress (0-2)",
        1: "Moderate stress (3-4)",
        2: "High stress (5-9)",
    },
}


def stress_to_class(value, num_classes):
    """Convert an original 0-9 stress score to a classification label."""
    score = int(float(value))
    if not 0 <= score <= 9:
        raise ValueError(f"Stress score must be between 0 and 9, got {score}")

    if num_classes == 2:
        return 0 if score <= 3 else 1
    if num_classes == 3:
        if score <= 2:
            return 0
        if score <= 4:
            return 1
        return 2
    if num_classes == 10:
        # Keep the original 0-9 score as its ten-class label.
        return score
    raise ValueError("--num_c must be 2, 3, or 10")


def find_label_column(df, ex):
    for column in LABEL_COLUMNS[ex]:
        if column in df.columns:
            return column
    raise KeyError(
        f"Cannot find the stress column for {ex}. "
        f"Tried: {LABEL_COLUMNS[ex]}"
    )


def subject_number(path):
    """Find S<number> in a video path, starting from the filename upward."""
    parts = [os.path.basename(path)] + list(reversed(os.path.normpath(path).split(os.sep)))
    for part in parts:
        match = re.search(r"(?:^|[-_])S(\d+)(?:[-_.]|$)", part, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def safe_movement_name(name):
    name = re.sub(r'[<>:"/\\|?*]', "_", name.strip())
    return re.sub(r"\s+", "_", name)


def movement_item_name(folder_name):
    """Convert a movement folder name to the standard English item name."""
    return MOVEMENT_FOLDER_TO_ITEM.get(
        folder_name, folder_name.replace("_", " ").strip()
    )


def video_frame_count(path):
    """Return the frame count reported by the video container."""
    capture = cv2.VideoCapture(path)
    if not capture.isOpened():
        capture.release()
        return None
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()
    return count if count > 0 else None


def discover_videos(data_root):
    """
    Expected layout:
      data_root/EX1|EX2|EX3/name/face|side/movement/video.mp4
    """
    groups = defaultdict(list)
    skipped_view = 0

    for root, _, files in os.walk(data_root):
        mp4_files = [
            f
            for f in files
            if f.lower().startswith("personclip") and f.lower().endswith(".mp4")
        ]
        if not mp4_files:
            continue

        relative = os.path.relpath(root, data_root)
        parts = relative.split(os.sep)
        ex_index = next(
            (i for i, part in enumerate(parts) if part.upper() in LABEL_COLUMNS),
            None,
        )
        if ex_index is None:
            continue

        ex = parts[ex_index].upper()
        view_index = next(
            (
                i
                for i in range(ex_index + 1, len(parts))
                if parts[i].lower() in {"face", "side"}
            ),
            None,
        )
        if view_index is None or view_index + 1 >= len(parts):
            skipped_view += len(mp4_files)
            continue

        view = parts[view_index].lower()
        movement_folder = parts[view_index + 1]
        movement = movement_item_name(movement_folder)
        for filename in mp4_files:
            groups[(ex, movement)].append(
                {
                    "path": os.path.abspath(os.path.join(root, filename)),
                    "view": view,
                    "movement_folder": movement_folder,
                }
            )

    return groups, skipped_view


def stratified_split(samples, ratio, seed):
    if not 0 <= ratio < 0.5:
        raise ValueError("--ratio must be >= 0 and < 0.5")

    by_class = defaultdict(list)
    for sample in samples:
        by_class[sample["label"]].append(sample)

    rng = random.Random(seed)
    train, val, test = [], [], []
    for label in sorted(by_class):
        items = by_class[label][:]
        rng.shuffle(items)
        n_val = int(len(items) * ratio)
        n_test = int(len(items) * ratio)

        # When possible, give both validation and test at least one sample.
        if ratio > 0 and len(items) >= 3:
            n_val = max(1, n_val)
            n_test = max(1, n_test)
        if n_val + n_test >= len(items):
            n_val = min(n_val, max(0, len(items) - 1))
            n_test = min(n_test, max(0, len(items) - n_val - 1))

        val.extend(items[:n_val])
        test.extend(items[n_val:n_val + n_test])
        train.extend(items[n_val + n_test:])

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


def write_data_file(path, samples):
    # VideoMAE list format: absolute_video_path class_label
    with open(path, "w", encoding="utf-8", newline="") as file:
        for sample in samples:
            file.write(f'{sample["path"]} {sample["label"]}\n')


def distribution(samples):
    return Counter(sample["label"] for sample in samples)


def print_and_write_statistics(output_dir, ex, movement, split_data, num_classes):
    stats_path = os.path.join(output_dir, "statistics.csv")
    labels = list(range(num_classes))
    with open(stats_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ex", "movement", "split", "view", "label", "class_name", "count"])

        print(f"\n[{ex}] {movement}")
        for split_name, samples in split_data.items():
            split_counter = distribution(samples)
            face_count = sum(s["view"] == "face" for s in samples)
            side_count = sum(s["view"] == "side" for s in samples)
            print(
                f"  {split_name:5s}: total={len(samples)}, "
                f"face={face_count}, side={side_count}, "
                f"labels={dict(sorted(split_counter.items()))}"
            )

            for view in ("all", "face", "side"):
                selected = samples if view == "all" else [
                    s for s in samples if s["view"] == view
                ]
                counts = distribution(selected)
                for label in labels:
                    class_name = CLASS_NAMES.get(num_classes, {}).get(
                        label, f"Original score {label}"
                    )
                    writer.writerow(
                        [
                            ex,
                            movement,
                            split_name,
                            view,
                            label,
                            class_name,
                            counts.get(label, 0),
                        ]
                    )


def main(args):
    if args.num_c not in {2, 3, 10}:
        raise ValueError("--num_c must be 2, 3, or 10")

    df = pd.read_excel(args.labelpath)
    label_series = {
        ex: df[find_label_column(df, ex)].reset_index(drop=True)
        for ex in LABEL_COLUMNS
    }

    groups, skipped_view = discover_videos(args.datapath)
    if not groups:
        raise RuntimeError(
            "No videos found under EX1/EX2/EX3/name/face|side/movement/"
        )

    os.makedirs(args.outdir, exist_ok=True)
    grand_total = Counter()
    processed_groups = 0
    short_videos = 0
    unreadable_videos = 0
    output_name_counts = Counter(
        safe_movement_name(movement) for _, movement in groups
    )

    for (ex, movement), videos in sorted(groups.items()):
        samples = []
        missing_subject = 0
        missing_label = 0

        for video in videos:
            frame_count = video_frame_count(video["path"])
            if frame_count is None:
                unreadable_videos += 1
                print(f'[SKIP unreadable] {video["path"]}')
                continue
            if frame_count < args.min_frames:
                short_videos += 1
                print(
                    f'[SKIP <{args.min_frames} frames] '
                    f'{video["path"]} ({frame_count} frames)'
                )
                continue

            number = subject_number(video["path"])
            if number is None:
                missing_subject += 1
                continue

            label_index = number + args.subject_offset
            if label_index < 0 or label_index >= len(label_series[ex]):
                missing_label += 1
                continue

            raw_stress = label_series[ex].iloc[label_index]
            if pd.isna(raw_stress):
                missing_label += 1
                continue

            label = stress_to_class(raw_stress, args.num_c)
            samples.append(
                {
                    **video,
                    "label": label,
                    "subject": number,
                    "frames": frame_count,
                }
            )
            grand_total[label] += 1

        if not samples:
            print(f"[SKIP] {ex}/{movement}: no video with a valid label")
            continue

        train, val, test = stratified_split(samples, args.ratio, args.seed)
        split_data = {"train": train, "val": val, "test": test}

        safe_name = safe_movement_name(movement)
        folder_name = f"{safe_name}_c{args.num_c}"
        if output_name_counts[safe_name] > 1:
            # Avoid mixing same-named movements belonging to different EX folders.
            folder_name = f"{ex}_{folder_name}"
        output_dir = os.path.join(args.outdir, folder_name)
        os.makedirs(output_dir, exist_ok=True)

        for split_name, split_samples in split_data.items():
            write_data_file(
                os.path.join(output_dir, f"{split_name}.csv"),
                split_samples,
            )

        print_and_write_statistics(
            output_dir, ex, movement, split_data, args.num_c
        )
        if missing_subject or missing_label:
            print(
                f"  skipped: no subject number={missing_subject}, "
                f"no label={missing_label}"
            )
        processed_groups += 1

    print("\n========== OVERALL STATISTICS ==========")
    print(f"Movement groups written: {processed_groups}")
    print(f"Videos outside face/side layout skipped: {skipped_view}")
    print(f"Videos shorter than {args.min_frames} frames skipped: {short_videos}")
    print(f"Unreadable videos skipped: {unreadable_videos}")
    print(f"Valid videos by class: {dict(sorted(grand_total.items()))}")
    print(f"Output root: {args.outdir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Prepare EX1/EX2/EX3 classification data files for VideoMAE"
    )
    parser.add_argument(
        "--datapath",
        type=str,
        default=(
            "/srv/storage/stars@storage3.sophia.fr/dlai/"
            "Dataset/Thesis_MovementClip_TAG_YOLO"
        ),
    )
    parser.add_argument(
        "--labelpath",
        type=str,
        default=(
            "/srv/storage/stars@storage3.sophia.fr/dlai/"
            "Dataset/DanceClip_TAG/stress_label_90.xlsx"
        ),
    )
    parser.add_argument("--num_c", type=int, choices=[2, 3, 10], required=True)
    parser.add_argument(
        "--outdir",
        type=str,
        default=(
            "/srv/storage/stars@storage3.sophia.fr/dlai/"
            "Dataset/Thesis_ex1_classification_datafile_311ratio"
        ),
    )
    parser.add_argument("--ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--min-frames",
        type=int,
        default=32,
        help="Skip videos shorter than this number of frames (default: 32)",
    )
    parser.add_argument(
        "--subject-offset",
        type=int,
        default=-1,
        help="Excel row index offset relative to S number (default: S1 -> row index 0)",
    )
    main(parser.parse_args())
