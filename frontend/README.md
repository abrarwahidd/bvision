# Bvision Frontend

Frontend React untuk platform belajar abjad BISINDO. Menyediakan halaman belajar, kamus, artikel, informasi BISINDO, dan kontak. Fitur deteksi kamera mengirim frame JPEG ke backend melalui WebSocket.

## Teknologi

- React 19 dan Create React App
- React Router DOM 7
- Browser APIs: `getUserMedia`, Canvas, WebSocket

## Menjalankan lokal

Prasyarat: Node.js 18+ dan npm.

Dari folder `frontend/`:

```bash
npm ci
```

Buat file `.env`:

```env
REACT_APP_WS_URL=ws://localhost:8000/ws
```

Jalankan development server:

```bash
npm start
```

Buka `http://localhost:3000`. Backend harus berjalan dan menyediakan endpoint `/ws` sebelum fitur kamera dapat digunakan.

## Environment variable

| Variable | Fungsi | Contoh lokal | Contoh production |
|---|---|---|---|
| `REACT_APP_WS_URL` | Alamat WebSocket backend | `ws://localhost:8000/ws` | `wss://<domain-railway>/ws` |

Variable `REACT_APP_*` dimasukkan ke bundle saat build. Setelah mengubah nilainya di Vercel, redeploy frontend. Situs HTTPS harus menggunakan `wss://`.

## Alur kamera

1. Pengguna memberi izin kamera melalui browser.
2. Frontend menggambar frame video ke Canvas.
3. Setiap 400 ms, frame dikirim sebagai JPEG blob (kualitas 50%) ke `REACT_APP_WS_URL`.
4. Frontend menerima teks prediksi dari backend dan menampilkan hasil atau memeriksa jawaban mode ujian.

Kamera hanya dapat digunakan pada secure context seperti HTTPS atau `localhost`, serta setelah izin diberikan.

## Perintah

```bash
npm start
```
Menjalankan development server di `http://localhost:3000`.

```bash
CI=true npm test -- --watchAll=false
```
Menjalankan test satu kali tanpa watch mode.

```bash
npm run build
```
Membangun bundle production di `build/`.

## Deploy ke Vercel

1. Impor repository GitHub ke Vercel.
2. Set **Root Directory** ke `frontend`.
3. Set environment variable production:

```text
REACT_APP_WS_URL=wss://<domain-railway>/ws
```

4. Deploy atau redeploy setelah variable ditambahkan.
5. Pastikan backend Railway aktif dan `ALLOWED_ORIGINS` backend berisi origin Vercel, misalnya `https://<domain-vercel>`.

## CI

Workflow GitHub Actions di `../.github/workflows/ci_cd.yml` menjalankan `npm ci`, test, dan production build pada push/pull request ke `main`. Workflow belum melakukan deployment ke Vercel; deployment dapat dikelola lewat integrasi GitHub Vercel.
