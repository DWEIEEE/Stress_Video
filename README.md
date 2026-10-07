# Movement-Level Stress Classification with VideoMAE

Research code for movement-level stress classification from dance videos. The primary implementation is an EX1 adaptation of VideoMAE; the video-preparation and label-visualization utilities are included as optional supporting tools.

> **Data and pretrained weights are deliberately not distributed in this repository.** They may contain sensitive participant material or be too large for ordinary Git hosting.

![Ground-truth dataset summary](docs/images/dataset_summary.png)

## What is included

| Component | Purpose | Status |
| --- | --- | --- |
| `src/videomae/` | Main VideoMAE fine-tuning and evaluation code | Primary code |
| `tools/video_preprocessing/` | Clips raw recordings and builds VideoMAE train/validation/test lists | Optional preprocessing |
| `tools/label_visualization/` | Inspects ground-truth CSV/XLSX labels and produces plots | Optional analysis |
| `scripts/train_ex1.sh` | Portable EX1 training launcher | Example configuration |

## Study summary

Each sample is a movement video labelled with a dancer's self-reported stress level. The EX1 experiments compare 2-class, 3-class, and 10-class stress classification. Splits are made **by participant**, so recordings from the same participant (including frontal and diagonal views) never appear in different splits. The intended train/validation/test proportions are 60% / 20% / 20%, with the final 18 participants reserved for testing.

## Repository layout

```text
Stress_Classification_Release/
├── src/videomae/                 # VideoMAE source and upstream documentation
├── tools/
│   ├── video_preprocessing/      # segmentation, cropping, dataset-list builders
│   └── label_visualization/      # ground-truth visualization utilities
├── scripts/train_ex1.sh          # fine-tuning example
├── docs/images/                  # README image only
├── third_party/videomae/         # retained upstream license and notices
├── requirements.txt
└── .gitignore
```

## Setup

Use Python 3.9 and an environment with a PyTorch build compatible with your CUDA driver. Install PyTorch and torchvision according to the [official selector](https://pytorch.org/get-started/locally/), then install the remaining packages:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Stress_Classification_Release
pip install -r requirements.txt
```


## Data preparation

The main data loader expects a directory containing `train.csv`, `val.csv`, and `test.csv`. Each row follows VideoMAE's format:

```text
/absolute/or/relative/path/to/video.mp4 class_id
```

Build EX1 list files from movement videos and an annotation spreadsheet:

```bash
python tools/video_preprocessing/Make_ex1_thesis_datafile.py \
  --datapath /path/to/movement_videos \
  --labelpath /path/to/stress_labels.xlsx \
  --num_c 2 \
  --outdir /path/to/ex1_lists
```

## Fine-tuning EX1

Download or otherwise provide a VideoMAE pretrained checkpoint, then use the release launcher:

```bash
bash scripts/train_ex1.sh \
  /path/to/ex1_lists \
  /path/to/videomae_pretrained_checkpoint.pth \
  /path/to/outputs
```

The launcher discovers movement directories named `<movement>_c2`, `<movement>_c3`, and `<movement>_c10`. It writes checkpoints and logs only below the output directory you provide. For a single run or additional options, call `src/videomae/run_class_finetuning.py --help`.

## Implementation details

Experiments were implemented in Python with PyTorch, OpenCV, NumPy, and timm, and were run on a single NVIDIA Quadro RTX 6000 GPU. The model is VideoMAE with a ViT-Base backbone initialized from Kinetics-400 pretrained weights.

- Video frames are resized while preserving aspect ratio, then spatially cropped to 224 × 224 pixels. The ViT uses non-overlapping 16 × 16 patches.
- Each input clip contains 16 frames sampled at temporal stride 2.
- Fine-tuning uses AdamW for 100 epochs with batch size 4, learning rate `1e-2`, weight decay `0.05`, and betas `(0.9, 0.999)`. No learning-rate warm-up is used.
- Unless otherwise stated, the random seed is 42. At inference, logits from all clips for the same video are averaged and the highest aggregated logit determines the video-level class.

The study used progressive unfreezing during fine-tuning. The archived source does not include the schedule controlling that unfreezing, so `scripts/train_ex1.sh` does not claim to reproduce it; define and document a schedule before using this release for an exact replication.

## Ground-truth label visualization

For a portable summary of ground-truth labels in CSV or XLSX format:

```bash
python tools/label_visualization/summarize_ground_truth.py \
  --input /path/to/ground_truth.csv \
  --columns stress_level age gender \
  --output docs/ground_truth_summary.png
```

The existing `label_summary.py` and notebook are retained as project-specific reference scripts. They contain the original study column names and a local spreadsheet path; use the new command-line script for new CSV files.

## References and attribution

The main model code is adapted from [VideoMAE](https://github.com/MCG-NJU/VideoMAE), "Masked Autoencoders are Data-Efficient Learners for Self-Supervised Video Pre-Training" (NeurIPS 2022). Its license and notices are retained in [`third_party/videomae/`](third_party/videomae/).

The video workflow can consume person-cropped videos produced using [YOLOv7](https://github.com/WongKinYiu/yolov7); YOLOv7 code and weights are not bundled here. Please follow each upstream project's license and cite the relevant work when publishing results.

