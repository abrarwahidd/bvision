# training/extract_landmarks.py
import os
import cv2
import mediapipe as mp
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Path (relatif dari root repo) ─────────────────────────────────────────────
DATASET_DIR = Path("data/raw")          # folder berisi subfolder A-Z
OUTPUT_PATH = Path("data/processed/landmarks.csv")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Inisialisasi Mediapipe ────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5
)

# ── Fungsi ekstraksi per gambar ───────────────────────────────────────────────
def extract_landmarks_from_image(image_path: Path) -> list | None:
    """
    Baca gambar, deteksi tangan, return list 84 nilai
    (x,y × 21 titik × 2 tangan).
    Return None kalau tidak ada tangan terdeteksi.
    """
    image = cv2.imread(str(image_path))
    if image is None:
        log.warning(f"Gagal membaca gambar: {image_path}")
        return None

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    if not results.multi_hand_landmarks:
        return None   # skip gambar tanpa tangan terdeteksi

    row = []
    num_hands = len(results.multi_hand_landmarks)

    for i in range(2):   # selalu 2 slot agar dimensi konsisten = 84
        if i < num_hands:
            for lm in results.multi_hand_landmarks[i].landmark:
                row.append(lm.x)
                row.append(lm.y)
        else:
            # tangan ke-2 tidak ada → padding nol
            row.extend([0.0] * 42)   # 21 titik × 2 (x, y)

    assert len(row) == 84, f"Dimensi tidak sesuai: {len(row)}"
    return row


# ── Main ──────────────────────────────────────────────────────────────────────
def run_extraction():
    if not DATASET_DIR.exists():
        raise FileNotFoundError(
            f"Folder dataset tidak ditemukan: {DATASET_DIR}\n"
            f"Pastikan gambar BISINDO ada di data/raw/<label>/"
        )

    label_folders = sorted([
        d for d in DATASET_DIR.iterdir() if d.is_dir()
    ])

    if not label_folders:
        raise ValueError(f"Tidak ada subfolder label di {DATASET_DIR}")

    log.info(f"Ditemukan {len(label_folders)} label: "
             f"{[d.name for d in label_folders]}")

    data    = []
    labels  = []
    skipped = 0

    for label_folder in label_folders:
        label = label_folder.name
        image_files = (
            list(label_folder.glob("*.jpg")) +
            list(label_folder.glob("*.jpeg")) +
            list(label_folder.glob("*.png"))
        )

        if not image_files:
            log.warning(f"Tidak ada gambar di folder: {label_folder}")
            continue

        log.info(f"Memproses label '{label}' — {len(image_files)} gambar")

        for img_path in tqdm(image_files, desc=label, leave=False):
            row = extract_landmarks_from_image(img_path)
            if row is None:
                skipped += 1
                continue
            data.append(row)
            labels.append(label)

    if not data:
        raise RuntimeError(
            "Tidak ada landmark yang berhasil diekstrak. Periksa dataset."
        )

    # Nama kolom: h0_lm0_x, h0_lm0_y, ..., h1_lm20_x, h1_lm20_y
    columns = []
    for hand_idx in range(2):
        for point_idx in range(21):
            columns.append(f"h{hand_idx}_lm{point_idx}_x")
            columns.append(f"h{hand_idx}_lm{point_idx}_y")

    df = pd.DataFrame(data, columns=columns)
    df["label"] = labels

    df.to_csv(OUTPUT_PATH, index=False)

    log.info(
        f"\n=== Ekstraksi Selesai ==="
        f"\nTotal data   : {len(df)}"
        f"\nSkipped      : {skipped} gambar (tidak ada tangan)"
        f"\nLabel        : {sorted(df['label'].unique())}"
        f"\nOutput       : {OUTPUT_PATH}"
    )
    print("\nDistribusi per label:")
    print(df["label"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    try:
        run_extraction()
    finally:
        hands.close()   # pastikan Mediapipe selalu di-release