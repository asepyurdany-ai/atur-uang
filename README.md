# Atur Uang 💰

Multi-project financial tracker — handled by Dexter via natural language commands.

No web UI. No Telegram bot. Just talk to Dexter.

---

## Cara Pakai

```
atur buat [nama project] [modal]
atur buat [nama] [modal] deskripsi [teks]
atur catat [project] [nominal] [keterangan]
atur saldo [project?]
atur laporan [project]
atur laporan [project] minggu ini
atur hapus [id transaksi]
atur list
atur bantuan
```

### Contoh

```
atur buat warung sembako 100jt
atur buat renovasi rumah 50jt deskripsi renovasi rumah pak asep

atur catat warung 2jt beli cat tembok
atur catat warung 500rb bayar tukang harian
atur catat renovasi 1.5jt beli meja kayu

atur saldo warung
atur saldo

atur laporan warung
atur laporan warung minggu ini

atur hapus 5
atur list
```

### Format Nominal

| Input     | Nilai         |
|-----------|---------------|
| `100jt`   | 100,000,000   |
| `2jt`     | 2,000,000     |
| `1.5jt`   | 1,500,000     |
| `500rb`   | 500,000       |
| `50000`   | 50,000        |

---

## Setup

```bash
cd /home/asepyudi/atur-uang
python3 -m venv .venv
source .venv/bin/activate
python main.py  # run test suite
```

---

## Integrasi Dexter

Dexter otomatis mendeteksi pesan yang diawali `atur` dan meneruskannya ke `handle_command()`.

```python
from atur_uang.main import handle_command, init_db
init_db()
response = handle_command("atur saldo warung")
```

---

## Auto-kategori

Transaksi dikategorikan otomatis berdasarkan keyword:

- **material** — cat, semen, kayu, besi, keramik, meja, ...
- **tukang** — tukang, mandor, upah, ongkos, ...
- **transport** — bensin, ojek, angkut, kirim, ...
- **admin** — izin, pajak, notaris, ...
- **stok** — beras, minyak, gula, sembako, ...
- **umum** — default jika tidak cocok

---

Built with ❤️ by Dexter for Asep.
