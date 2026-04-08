import re
import sys
import os

# Allow running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import (
    init_db, create_project, list_projects, get_project,
    add_transaction, delete_transaction, get_transactions, get_summary
)
from formatter import (
    fmt_buat, fmt_catat, fmt_saldo, fmt_saldo_all, fmt_laporan,
    fmt_hapus, fmt_list, fmt_bantuan, fmt_error
)

# ─── Category auto-detection ──────────────────────────────────────────────────

CATEGORIES = {
    'material': ['cat', 'semen', 'bata', 'kayu', 'besi', 'paku', 'genteng', 'keramik',
                 'meja', 'kursi', 'rak', 'etalase', 'kulkas', 'timbangan'],
    'tukang':   ['tukang', 'mandor', 'kuli', 'upah', 'ongkos', 'kerja'],
    'transport': ['bensin', 'ojek', 'angkut', 'kirim', 'transport'],
    'admin':    ['izin', 'surat', 'pajak', 'notaris', 'admin'],
    'stok':     ['stok', 'barang', 'dagangan', 'sembako', 'beras', 'minyak', 'gula'],
}


def detect_category(text: str) -> str:
    text_lower = text.lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text_lower:
                return cat
    return 'umum'


# ─── Amount parser ────────────────────────────────────────────────────────────

def parse_amount(s: str) -> int:
    """
    Parse Indonesian amount shorthand.
    100jt → 100_000_000
    2jt   → 2_000_000
    500rb → 500_000
    1.5jt → 1_500_000
    50000 → 50_000
    2,500,000 → 2_500_000
    2.500.000 → 2_500_000
    """
    s = s.strip().lower().replace(" ", "")

    # Handle juta shorthand
    m = re.match(r'^([\d.,]+)\s*jt$', s)
    if m:
        num_str = m.group(1).replace(",", ".")
        return int(float(num_str) * 1_000_000)

    # Handle ribu shorthand (rb / k)
    m = re.match(r'^([\d.,]+)\s*(rb|ribu|k)$', s)
    if m:
        num_str = m.group(1).replace(",", ".")
        return int(float(num_str) * 1_000)

    # Handle numeric with separators
    # "2,500,000" or "2.500.000"
    # Detect: if there are multiple separators of same kind, strip them
    # If ends with 3 digits after last separator, treat all as thousand-sep
    clean = s

    # Comma-separated thousands: 2,500,000
    if re.match(r'^\d{1,3}(,\d{3})+$', clean):
        return int(clean.replace(",", ""))

    # Dot-separated thousands: 2.500.000
    if re.match(r'^\d{1,3}(\.\d{3})+$', clean):
        return int(clean.replace(".", ""))

    # Plain integer
    try:
        return int(float(clean.replace(",", ".")))
    except ValueError:
        raise ValueError(f"Tidak bisa parse nominal: '{s}'")


# ─── Command parser ───────────────────────────────────────────────────────────

AMOUNT_PATTERN = r'(\d[\d.,]*(?:\s*(?:jt|rb|ribu|k))?)'


def parse_command(text: str) -> dict:
    """Parse natural language atur-uang commands."""
    text = text.strip()

    # Must start with 'devi'
    if not re.match(r'^devi\b', text, re.IGNORECASE):
        return {"action": None}

    # Strip leading "devi "
    body = re.sub(r'^devi\s*', '', text, flags=re.IGNORECASE).strip()

    # ── bantuan / help ──
    if re.match(r'^(bantuan|help|\\?)$', body, re.IGNORECASE):
        return {"action": "bantuan"}

    # ── list ──
    if re.match(r'^list$', body, re.IGNORECASE):
        return {"action": "list"}

    # ── hapus <id> ──
    m = re.match(r'^hapus\s+(\d+)$', body, re.IGNORECASE)
    if m:
        return {"action": "hapus", "tx_id": int(m.group(1))}

    # ── saldo [project] ──
    m = re.match(r'^saldo(?:\s+(.+))?$', body, re.IGNORECASE)
    if m:
        project = m.group(1).strip() if m.group(1) else None
        return {"action": "saldo", "project": project}

    # ── laporan <project> [minggu ini / bulan ini] ──
    m = re.match(r'^laporan\s+(.+?)(?:\s+(minggu ini|bulan ini|7 hari|30 hari))?$', body, re.IGNORECASE)
    if m:
        project = m.group(1).strip()
        period_str = m.group(2)
        period = None
        if period_str:
            period_str_low = period_str.lower()
            if 'minggu' in period_str_low or '7' in period_str_low:
                period = 7
            elif 'bulan' in period_str_low or '30' in period_str_low:
                period = 30
        return {"action": "laporan", "project": project, "period": period}

    # ── buat <project> <pool> [deskripsi <text>] ──
    # Format: buat <name tokens> <amount> [deskripsi <text>]
    m = re.match(
        r'^buat\s+(.+?)\s+' + AMOUNT_PATTERN + r'(?:\s+deskripsi\s+(.+))?$',
        body, re.IGNORECASE
    )
    if m:
        project = m.group(1).strip()
        pool_str = m.group(2).strip()
        desc = m.group(3).strip() if m.group(3) else ""
        try:
            pool = parse_amount(pool_str)
        except ValueError as e:
            return {"action": "error", "message": str(e)}
        return {"action": "buat", "project": project, "pool": pool, "description": desc}

    # ── catat <project> <amount> <description> ──
    # Format: catat <project_name> <amount> <desc...>
    m = re.match(
        r'^catat\s+(.+?)\s+' + AMOUNT_PATTERN + r'\s+(.+)$',
        body, re.IGNORECASE
    )
    if m:
        project = m.group(1).strip()
        amount_str = m.group(2).strip()
        desc = m.group(3).strip()
        try:
            amount = parse_amount(amount_str)
        except ValueError as e:
            return {"action": "error", "message": str(e)}
        return {"action": "catat", "project": project, "amount": amount, "desc": desc}

    return {"action": "unknown", "body": body}


# ─── Command handler ──────────────────────────────────────────────────────────

def handle_command(text: str) -> str:
    cmd = parse_command(text)
    action = cmd.get("action")

    if action is None:
        return ""  # Not an atur command

    if action == "bantuan":
        return fmt_bantuan()

    if action == "list":
        projects = list_projects()
        return fmt_list(projects)

    if action == "hapus":
        tx = delete_transaction(cmd["tx_id"])
        if tx is None:
            return fmt_error(f"Transaksi #{cmd['tx_id']} tidak ditemukan.")
        return fmt_hapus(tx)

    if action == "saldo":
        project_name = cmd.get("project")
        if project_name:
            summary = get_summary(project_name)
            if summary is None:
                return fmt_error(f'Project "{project_name}" tidak ditemukan.')
            return fmt_saldo(summary)
        else:
            projects = list_projects()
            return fmt_saldo_all(projects)

    if action == "laporan":
        data = get_transactions(cmd["project"], days=cmd.get("period"))
        if data is None:
            return fmt_error(f'Project "{cmd["project"]}" tidak ditemukan.')
        return fmt_laporan(data)

    if action == "buat":
        existing = get_project(cmd["project"])
        if existing and existing["name"].lower() == cmd["project"].lower():
            return fmt_error(f'Project "{cmd["project"]}" sudah ada.')
        project = create_project(cmd["project"], cmd["pool"], cmd.get("description", ""))
        if project is None:
            return fmt_error(f'Project "{cmd["project"]}" sudah ada.')
        return fmt_buat(project)

    if action == "catat":
        category = detect_category(cmd["desc"])
        tx = add_transaction(cmd["project"], cmd["amount"], cmd["desc"], category)
        if tx is None:
            return fmt_error(f'Project "{cmd["project"]}" tidak ditemukan.')
        return fmt_catat(tx)

    if action == "error":
        return fmt_error(cmd.get("message", "Perintah tidak dikenali."))

    if action == "unknown":
        return fmt_error(
            f'Perintah tidak dikenali: "devi {cmd.get("body", "")}".\n'
            'Ketik "devi bantuan" untuk melihat daftar perintah.'
        )

    return fmt_error("Perintah tidak dikenali.")


# ─── CLI entrypoint ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()

    # If argument given, handle as single command
    if len(sys.argv) > 1:
        cmd_text = " ".join(sys.argv[1:])
        print(handle_command(cmd_text))
        sys.exit(0)

    # Test suite
    tests = [
        "devi buat warung sembako 100jt",
        "devi catat warung 2jt beli cat tembok",
        "devi catat warung 500rb bayar tukang harian",
        "devi catat warung 1.5jt beli meja kayu",
        "devi saldo warung",
        "devi laporan warung",
        "devi list",
        "devi bantuan",
    ]
    for cmd in tests:
        print(f"\n>>> {cmd}")
        print(handle_command(cmd))
