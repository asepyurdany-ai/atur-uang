# Atur Uang 💰

Multi-project financial tracker — handled by Dexter via natural language commands.

No web UI. No Telegram bot. Just talk to Dexter.

---

## Cara Pakai

```
devi buat [nama project] [modal]
devi buat [nama] [modal] deskripsi [teks]
devi catat [project] [nominal] [keterangan]
devi saldo [project?]
devi laporan [project]
devi laporan [project] minggu ini
devi hapus [id transaksi]
devi list
devi bantuan
```

### Contoh

```
devi buat warung sembako 100jt
devi buat renovasi rumah 50jt deskripsi renovasi rumah pak asep

devi catat warung 2jt beli cat tembok
devi catat warung 500rb bayar tukang harian
devi catat renovasi 1.5jt beli meja kayu

devi saldo warung
devi saldo

devi laporan warung
devi laporan warung minggu ini

devi hapus 5
devi list
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
response = handle_command("devi saldo warung")
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
