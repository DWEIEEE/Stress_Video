from moviepy import VideoFileClip
import argparse
import glob
import os
from collections import defaultdict, Counter
import unicodedata

movement_translation = {
    # EX1
    "preparation en musique": "音樂準備",
    "demi-plie 1ere": "第一位置半蹲",
    "demi-plie 2e": "第二位置半蹲",
    "demi-plie 4e": "第四位置半蹲",
    "demi-plie 5e": "第五位置半蹲",
    "grand-plie 1ere": "第一位置深蹲",
    "grand-plie 2e": "第二位置深蹲",
    "grand plie 4e": "第四位置深蹲",
    "grand-plie 5e": "第五位置深蹲",
    "penche en avant 1ere": "第一位置前傾",
    "penche en avant 4e": "第四位置前傾",
    "penche cote barre": "向扶桿側傾",
    "penche exterieur": "向外側傾",
    "equilibre 1ere": "第一位置平衡",
    "equilibre": "平衡動作",
    "cambre 4e": "第四位置後仰",
    "transition 2e": "第二位置轉換",
    "transition 4e": "第四位置轉換",
    "transition 5e": "第五位置轉換",
    "tout le tour": "全身旋轉",
    "etire de bras": "手臂伸展",
    "conclusion": "結尾",
    "erreur": "錯誤標記",
    # EX2
    "preparation": "音樂準備",
    "frappe double cote": "雙擊側面",
    "frappe simple cote": "單擊側面",
    "3 ronds simples seconde": "三個簡單圓形動作（第二位置）",
    "battu a la cheville": "腳踝處的擊步",
    "frappe double derriere": "雙擊後方",
    "frappe simple derriere": "單擊後方",
    "frappe double devant": "雙擊前方",
    "frappe simple devant": "單擊前方",
    "pas de gigue releve": "蘇格蘭踢步提升",
    "equilibre cheville derriere": "後腳踝平衡",
    "equilibre cheville devant": "前腳踝平衡",
        
    # EX3
    "battement cote rapide": "側向擊腿（快速）",
    "battement d der rapide": "右腳後擊腿（快速）",
    "battement d dev rapide": "右腳前擊腿（快速）",
    "battement g der rapide": "左腳後擊腿（快速）",
    "battement g dev rapide": "左腳前擊腿（快速）",

    "battement cote lent": "側向擊腿（慢速）",
    "battement d der lent": "右腳後擊腿（慢速）",
    "battement g der lent": "左腳後擊腿（慢速）",
    "battement g dev lent": "左腳前擊腿（慢速）",
    "battement d dev lent": "右腳前擊腿（慢速）",

    "penche en arriere": "後傾",
    "penche en avant": "前傾",

    "preparation": "準備動作",
    "conclusion": "結尾"
}

def main(kwargs):

    data_path = kwargs["path"]
    keyword = kwargs["keyword"]

    if not os.path.exists(data_path):
        print(f"The Path does not exist ...")
        return

    basename = os.path.basename(data_path)

    num = 1

    storage = []
    per_dancer_movements = {}
    movement_summary = defaultdict(int) 
    movement_coverage = defaultdict(int)  
    while True:
        if num == 26 or num== 25:
            num += 1
            continue
        if num > 52:
            break
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

        rows = read_file(anno_path, keyword)
        counts = print_per_file_outcome(anno_path, rows)
        for mv, c in counts.items():
            movement_summary[mv] += c
        dancer_id = rows[0]["dancer"]

        mv_set = {r["movement"] for r in rows if r.get("movement")}
        per_dancer_movements[dancer_id] = mv_set

        for mv in mv_set:
            movement_coverage[mv] += 1

        storage.extend(rows)
        num += 1

    print(f"Total Dancer : {num-2}")
    print("\n--- 全部動作統計 ---")
    sorted_total = sorted(movement_summary.items(), key=lambda x: (-x[1], x[0]))
    dancer_id = rows[0]["dancer"] if rows else f"S{num}"
    mv_set = {r["movement"] for r in rows if r.get("movement")}
    per_dancer_movements[dancer_id] = mv_set
    for mv, cnt in sorted_total:
        print(f"{mv} ({movement_translation[remove_accents(mv.lower())]}): {cnt}")

    all_sets = list(per_dancer_movements.values())
    common_movements = set.intersection(*all_sets) if len(all_sets) > 1 else set(all_sets[0])
    common_movements = sorted(common_movements)

    print("\n=== 每位舞者都共有的動作（交集） ===")
    if common_movements:
        for mv in common_movements:
            print(f"{mv} ({movement_translation[remove_accents(mv.lower())]})")
    else:
        print("（無共同動作）")

    # 另外列出「動作覆蓋率」（每個動作在多少舞者中出現）
    print("\n=== 動作覆蓋率（動作 -> 有出現的舞者數 / 總舞者數） ===")
    for mv, cnt in sorted(movement_coverage.items(), key=lambda x: (-x[1], x[0])):
        print(f"{mv} ({movement_translation[remove_accents(mv.lower())]}): {cnt}/{num-2}")
        
def print_per_file_outcome(file_path, kept_rows):
    """印出每個檔案的結果摘要與動作統計。"""
    if not kept_rows:
        print(f"[{os.path.basename(file_path)}] 無符合關鍵字的資料列。")
        return

    total_segments = len(kept_rows)
    durations = [r["duration"] for r in kept_rows if isinstance(r["duration"], (int, float))]
    ends = [r["end"] for r in kept_rows if isinstance(r["end"], (int, float))]

    total_duration = round(sum(d for d in durations if d is not None), 3) if durations else 0.0
    last_end = round(max(ends), 3) if ends else None

    # 動作統計 (Counter)
    movement_counts = Counter(r["movement"] for r in kept_rows if r["movement"])
    uniq_movements = list(movement_counts.keys())

    print(f"\n[{os.path.basename(file_path)}] "
          f"總持續時間={total_duration}s, "
          f"動作種類={len(uniq_movements)}")

    # 印出動作出現次數
    sorted_mv = sorted(movement_counts.items(), key=lambda x: (-x[1], x[0]))
    preview = ", ".join([f"{k}: {v}" for k, v in sorted_mv])
    print(f"  動作統計: {preview}")

    return movement_counts
    
def read_file(path, keyword):
    rows = []
    kw = keyword.lower()
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            ln = raw.strip()
            if not ln:
                continue
            parts = ln.split("\t")
            if len(parts) < 6:
                continue  # 跳過格式錯誤的列

            type_col = parts[0].strip()
            # 檢查第一欄是否以 keyword 開頭（不分大小寫）
            if not type_col.lower().startswith(kw):
                continue

            session = parts[1].strip()

            def _to_float(x):
                try:
                    return float(x)
                except Exception:
                    return None

            start = _to_float(parts[2].strip())
            end = _to_float(parts[3].strip())
            duration = _to_float(parts[4].strip())
            movement = "\t".join(parts[5:]).strip()

            rows.append({
                "dancer": session,
                "kw": type_col,
                "start": start,
                "end": end,
                "duration": duration,
                "movement": movement
            })
    return rows

def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

def check_exist(path):
    if os.path.exists(path):
        return True
    return False

if __name__ == "__main__":
    # python anno_organize.py --path "/srv/storage/stars@storage3.sophia.grid5000.fr/qmerille/qmerille/workspace/dataset/danse/EX1"
    
    parser = argparse.ArgumentParser(description="organize the dancer movement")

    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--keyword", type=str, default="execution reelle")

    args = parser.parse_args()
    kwargs = vars(args)
    main(kwargs)
