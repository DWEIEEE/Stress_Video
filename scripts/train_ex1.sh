#!/usr/bin/env bash
# Fine-tune VideoMAE separately for each EX1 movement and class setting.
# Usage: bash scripts/train_ex1.sh <dataset-root> <pretrained-checkpoint> [output-root]

set -euo pipefail

DATASET_ROOT=${1:?"Usage: bash scripts/train_ex1.sh <dataset-root> <pretrained-checkpoint> [output-root]"}
PRETRAINED_CHECKPOINT=${2:?"A VideoMAE pretrained checkpoint is required"}
OUTPUT_ROOT=${3:-"outputs/ex1"}

REPOSITORY_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MODEL_DIR="${REPOSITORY_ROOT}/src/videomae"

if [[ ! -f "${PRETRAINED_CHECKPOINT}" ]]; then
  echo "Checkpoint not found: ${PRETRAINED_CHECKPOINT}" >&2
  exit 1
fi

for NUM_CLASSES in 2 3 10; do
  shopt -s nullglob
  DATASET_DIRS=("${DATASET_ROOT}"/*_c"${NUM_CLASSES}")
  shopt -u nullglob

  for DATASET_DIR in "${DATASET_DIRS[@]}"; do
    MOVEMENT=$(basename "${DATASET_DIR%_c${NUM_CLASSES}}")
    OUTPUT_DIR="${OUTPUT_ROOT}/${MOVEMENT}_c${NUM_CLASSES}"
    mkdir -p "${OUTPUT_DIR}"

    echo "Training ${MOVEMENT} (${NUM_CLASSES} classes)"
    OMP_NUM_THREADS=1 python -u "${MODEL_DIR}/run_class_finetuning.py" \
      --model vit_base_patch16_224 \
      --data_set Kinetics-400 \
      --nb_classes "${NUM_CLASSES}" \
      --data_path "${DATASET_DIR}" \
      --finetune "${PRETRAINED_CHECKPOINT}" \
      --log_dir "${OUTPUT_DIR}" \
      --output_dir "${OUTPUT_DIR}" \
      --batch_size 4 \
      --num_sample 1 \
      --input_size 224 \
      --short_side_size 224 \
      --num_frames 16 \
      --sampling_rate 2 \
      --opt adamw \
      --lr 1e-2 \
      --opt_betas 0.9 0.999 \
      --weight_decay 0.05 \
      --epochs 100 \
      --warmup_epochs 0 \
      --layer_decay 1.0 \
      --seed 42 \
      --test_num_segment 5 \
      --test_num_crop 3 \
      --dist_eval \
      --no_auto_resume
  done
done
