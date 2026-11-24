# Bvision — Platform Belajar Abjad BISINDO Interaktif

Bvision adalah aplikasi web untuk mempelajari abjad Bahasa Isyarat Indonesia (BISINDO). Frontend React mengambil frame dari kamera pengguna dan mengirimkannya ke backend FastAPI melalui WebSocket untuk diprediksi menjadi huruf.

![Hero Bvision](frontend/public/asetreadme/image.png)

## Fitur

- **Deteksi bebas:** prediksi huruf BISINDO dari kamera secara real-time.
- **Mode ujian:** tantangan huruf acak dengan umpan balik.
- **Kamus:** referensi visual abjad, angka, dan kosakata.
- **Artikel:** informasi tentang bahasa isyarat dan budaya Tuli.
- **Responsif:** tampilan desktop dan perangkat mobile.

## Teknologi

| Bagian | Teknologi |
|---|---|
| Frontend | React 19, React Router, WebSocket API browser |
| Backend | Python 3.12, FastAPI, Uvicorn |
| Computer vision | MediaPipe 0.10.21, OpenCV headless |
| Klasifikasi | scikit-learn 1.9.1, joblib |
| Deployment | Vercel (frontend), Railway (backend) |
| Training/eksperimen | scikit-learn, MLflow; skrip di `training/` |

## Arsitektur inferensi

```text
Kamera browser
  → Canvas/JPEG setiap 400 ms
  → WebSocket /ws
  → FastAPI menerima bytes
  → OpenCV decode dan konversi RGB
  → MediaPipe Hands mendeteksi landmark
  → 84 fitur x/y dinormalisasi dengan StandardScaler
  → model Random Forest memprediksi huruf
  → backend mengirim teks prediksi ke browser
```

Model aktif dan scaler harus selalu dipasangkan:

- `backend/models/model_new.pkl`
- `backend/models/scaler_new.pkl`

Model pickle/joblib hanya boleh dimuat dari sumber tepercaya. Versi scikit-learn runtime harus cocok dengan versi saat artefak dibuat; backend mengunci `scikit-learn==1.9.1`.

## Struktur repository

```text
.
├── .github/workflows/ci_cd.yml # CI: test/build frontend, cek backend, build image
├── backend/
│   ├── main.py                 # FastAPI dan WebSocket /ws
│   ├── models/                 # Model dan scaler
│   ├── Dockerfile              # Image backend Railway/Docker
│   ├── nixpacks.toml            # Konfigurasi alternatif Railway Nixpacks
│   ├── pyproject.toml
│   └── uv.lock
├── data/
│   ├── raw/                    # Dataset training lokal, tidak dilacak Git
│   └── processed/              # Landmark CSV hasil ekstraksi, diabaikan Git
├── frontend/
│   ├── public/                 # Gambar, ikon, video kamus
│   └── src/                    # Halaman dan komponen React
├── metrics/                    # Output evaluasi lokal, diabaikan Git
├── mlartifacts/                # Artefak MLflow lokal, diabaikan Git
├── training/
│   ├── extract_landmarks.py    # Ekstraksi landmark dari data/raw/<label>/
│   ├── train.py                # Training, evaluasi, logging MLflow
│   └── params.yaml             # Parameter training dan MLflow
├── requirements-training.txt   # Dependency training
└── pyproject.toml              # Dependency tool training/MLflow
```

Dataset mentah di `data/raw/` tidak dilacak Git.

## Prasyarat

- Python 3.12+
- `uv` untuk backend dan environment training
- Node.js 18+ dan npm
- Webcam dan browser modern
- `libgl1` dan `libglib2.0-0` pada Linux jika diperlukan oleh OpenCV/MediaPipe

## Menjalankan lokal

### Backend

```bash
cd backend
uv sync --frozen
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend berjalan di `http://localhost:8000`; WebSocket di `ws://localhost:8000/ws`.

### Frontend

Di terminal terpisah:

```bash
cd frontend
npm ci
```

Buat `frontend/.env`:

```env
REACT_APP_WS_URL=ws://localhost:8000/ws
```

Jalankan frontend:

```bash
npm start
```

Buka `http://localhost:3000`, masuk **Belajar**, izinkan akses kamera, lalu pilih **Mulai Kamera**.

## Environment variables

| Variable | Lokasi | Nilai |
|---|---|---|
| `REACT_APP_WS_URL` | `frontend/.env` atau Vercel | URL WebSocket lengkap, misalnya `ws://localhost:8000/ws` lokal atau `wss://<domain-railway>/ws` production |
| `ALLOWED_ORIGINS` | Backend/Railway | Origin frontend yang diizinkan, misalnya `https://<domain-vercel>`; backend saat ini default `*` |

`REACT_APP_WS_URL` tertanam saat frontend dibuild. Setelah mengubah variable di Vercel, lakukan redeploy frontend.

## Training model (opsional)

Training terpisah dari backend serving. Siapkan gambar berlabel di `data/raw/<huruf>/`, lalu jalankan dari root repository:

```bash
uv sync
uv run python training/extract_landmarks.py
uv run python training/train.py
```

Konfigurasi dataset, split, model, dan MLflow ada di `training/params.yaml`. MLflow diarahkan ke `http://localhost:5000`; jalankan tracking server terlebih dahulu jika ingin UI tracking:

```bash
uv run mlflow server --host 127.0.0.1 --port 5000
```

Output training meliputi `data/processed/landmarks.csv`, `metrics/`, artefak MLflow lokal, dan pasangan model/scaler di `backend/models/`.

## Test dan build frontend

```bash
cd frontend
npm ci
CI=true npm test -- --watchAll=false
npm run build
```

Workflow GitHub Actions di `.github/workflows/ci_cd.yml` menjalankan test/build frontend, pemeriksaan sintaks backend dan keberadaan model, serta build Docker image pada push/pull request ke `main`. Workflow ini **belum melakukan deploy**. Railway dapat deploy otomatis dengan menghubungkan service ke repository dan branch yang dipilih.

## Deploy

### Backend ke Railway

1. Hubungkan repository GitHub ke Railway.
2. Set root directory service ke `/backend`.
3. Pilih build dari `backend/Dockerfile`.
4. Buat domain publik dan pastikan target port mengikuti `$PORT` Railway.
5. Set `ALLOWED_ORIGINS=https://<domain-vercel>`.
6. Periksa deployment log; Uvicorn harus listen di `0.0.0.0:$PORT` dan model/scaler berhasil dimuat.

Dockerfile menjalankan backend pada port `$PORT` (fallback `8000`). Jika memakai Nixpacks, `backend/nixpacks.toml` menyediakan install dan start command yang sesuai.

### Frontend ke Vercel

1. Impor repository ke Vercel.
2. Set **Root Directory** ke `frontend`.
3. Tambahkan environment variable:

```text
REACT_APP_WS_URL=wss://<domain-railway>/ws
```

4. Deploy/redeploy frontend setelah variable diset.

## Catatan integrasi dan privasi

- Browser production memerlukan `wss://` karena situs menggunakan HTTPS.
- Kamera hanya diakses setelah izin pengguna. Frame JPEG dikirim ke backend setiap 400 ms selama sesi kamera aktif.
- Jangan log atau menyimpan frame kamera tanpa kebutuhan dan persetujuan yang jelas.
- CI memeriksa kode dan build; belum ada monitoring prediksi produksi atau retraining otomatis.

## Pengembang

**Abrar Wahid** — [GitHub](https://github.com/abrarwahidd)
