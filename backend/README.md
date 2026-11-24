# Bvision Backend

Backend Bvision menyediakan inferensi klasifikasi abjad BISINDO melalui WebSocket. Browser mengirim frame JPEG dari kamera; FastAPI mengembalikan teks hasil prediksi.

## Stack

- Python 3.12
- FastAPI dan Uvicorn
- MediaPipe Hands untuk deteksi landmark
- OpenCV headless untuk decode frame
- scikit-learn 1.9.1 dan joblib untuk inferensi model

## Menjalankan lokal

Dari folder `backend/`:

```bash
uv sync --frozen
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

WebSocket tersedia di `ws://localhost:8000/ws`.

## Model

Backend memuat dua artefak saat proses mulai:

- `models/model_new.pkl`
- `models/scaler_new.pkl`

Keduanya harus tersedia dan berasal dari sumber tepercaya. Model dibuat dengan scikit-learn 1.9.1; dependency backend dikunci agar sesuai. Jika startup gagal, periksa log Railway atau terminal untuk file model dan error dependency.

## Protokol WebSocket

Endpoint: `/ws`

1. Client membuka koneksi WebSocket.
2. Client mengirim bytes gambar JPEG.
3. Backend mendecode gambar, mendeteksi tangan, mengekstrak 84 fitur koordinat landmark, melakukan scaling dan prediksi.
4. Backend membalas string label prediksi. Jika tangan tidak ditemukan atau frame tidak valid, hasilnya `Tidak Terdeteksi`.

Frontend saat ini mengirim frame tiap 400 ms dengan kualitas JPEG 50%.

## Environment variables

| Variable | Fungsi | Default |
|---|---|---|
| `PORT` | Port HTTP/WebSocket yang di-bind saat deploy | `8000` di Dockerfile; Railway menyediakan nilai saat runtime |
| `ALLOWED_ORIGINS` | Daftar origin frontend dipisahkan koma | `*` |

Contoh Railway:

```text
ALLOWED_ORIGINS=https://<domain-vercel>
```

`ALLOWED_ORIGINS` mengatur middleware CORS HTTP. Pastikan URL WebSocket frontend benar dan service Railway mengarahkan domain ke port yang sama dengan `$PORT`.

## Docker

Dari root repository:

```bash
docker build -t bvision-backend ./backend
docker run --rm -p 8000:8000 bvision-backend
```

Image memakai Python 3.12, memasang dependency dari `pyproject.toml` dan `uv.lock`, serta menjalankan Uvicorn pada `$PORT` (fallback `8000`). File model disertakan melalui Docker build context `backend/`.

## Deploy ke Railway

1. Hubungkan repository GitHub ke Railway.
2. Set root directory service ke `/backend`.
3. Gunakan `backend/Dockerfile` sebagai build method.
4. Generate domain publik dan pastikan target port domain mengikuti nilai `PORT` yang dipakai Uvicorn.
5. Set `ALLOWED_ORIGINS` ke domain frontend Vercel.
6. Deploy dan cek logs. Startup harus menunjukkan Uvicorn aktif tanpa error memuat model/scaler.

`nixpacks.toml` tersedia sebagai konfigurasi alternatif; jangan mencampur start command Nixpacks dengan asumsi Dockerfile.

## Catatan operasi

- Backend tidak melatih model saat startup; training ada di `../training/`.
- Koneksi WebSocket yang gagal sering tampak sebagai handshake `502`. Cocokkan port target Railway dengan port Uvicorn pada log, lalu periksa domain `/ws`.
- Jangan merekam atau menyimpan frame kamera di log tanpa kebutuhan, persetujuan, dan kebijakan retensi yang jelas.
- Model pickle/joblib hanya boleh dimuat dari artefak tepercaya karena format ini dapat menjalankan kode saat dimuat.
