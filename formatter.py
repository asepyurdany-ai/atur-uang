def fmt_rp(amount):
    """Format integer as Rp 1,000,000"""
    return f"Rp {amount:,}".replace(",", ".")


def fmt_buat(project):
    return (
        f'✅ Project "{project["name"].title()}" dibuat!\n'
        f'   Pool    : {fmt_rp(project["pool"])}\n'
        f'   Balance : {fmt_rp(project["balance"])}\n'
        f'   ID      : {project["id"]}'
    )


def fmt_catat(tx):
    return (
        f'✅ Tercatat!\n'
        f'   Project : {tx["project_name"].title()}\n'
        f'   Keluar  : -{fmt_rp(tx["amount"])} ({tx["description"]})\n'
        f'   Balance : {fmt_rp(tx["balance"])}'
    )


def fmt_saldo(summary):
    sep = "   " + "─" * 25
    lines = [
        f'📊 {summary["project_name"].title()}',
        f'   Pool    : {fmt_rp(summary["pool"])}',
        f'   Keluar  : {fmt_rp(summary["total_spent"])} ({summary["tx_count"]} transaksi)',
        f'   Sisa    : {fmt_rp(summary["balance"])}',
        sep,
    ]
    for cat, amt in sorted(summary["by_category"].items(), key=lambda x: -x[1]):
        label = cat.capitalize()
        lines.append(f'   {label:<10}: {fmt_rp(amt)}')
    if not summary["by_category"]:
        lines.append("   (belum ada transaksi)")
    return "\n".join(lines)


def fmt_saldo_all(projects):
    if not projects:
        return "📊 Belum ada project. Buat dulu: devi buat [nama] [modal]"
    lines = ["📊 Semua Project:"]
    for i, p in enumerate(projects, 1):
        lines.append(
            f'   {i}. {p["name"].title():<20} — Sisa {fmt_rp(p["balance"])} / {fmt_rp(p["pool"])}'
        )
    return "\n".join(lines)


def fmt_laporan(data):
    txs = data["transactions"]
    lines = [
        f'📋 Laporan {data["project_name"].title()}',
        f'   Pool  : {fmt_rp(data["pool"])}',
        f'   {"─"*50}',
        f'   {"No":<4} {"Tgl":<8} {"Nominal":>14}  Keterangan',
        f'   {"─"*50}',
    ]
    no = 1
    if not txs:
        lines.append("   (belum ada transaksi)")
    for tx in txs:
        # date: YYYY-MM-DD → DD Mon
        try:
            from datetime import datetime
            d = datetime.strptime(tx["date"], "%Y-%m-%d")
            date_str = d.strftime("%d %b")
        except Exception:
            date_str = tx["date"]
        lines.append(f'   {no:>2}. {date_str}  {fmt_rp(tx["amount"]):>14}  {tx["description"]}')
        no += 1
    total = sum(t["amount"] for t in txs)
    lines.append(f'   {"─"*50}')
    lines.append(f'   Total keluar : {fmt_rp(total)}')
    lines.append(f'   Sisa modal   : {fmt_rp(data["pool"] - total)}')
    return "\n".join(lines)


def fmt_hapus(tx):
    return (
        f'🗑 Transaksi #{tx["id"]} dihapus ({fmt_rp(tx["amount"])} — {tx["description"]})\n'
        f'   Balance baru: {fmt_rp(tx["balance"])}'
    )


def fmt_list(projects):
    if not projects:
        return "📋 Belum ada project."
    lines = ["📋 Daftar Project:"]
    for p in projects:
        desc = f" — {p['description']}" if p.get("description") else ""
        lines.append(
            f'   [{p["id"]}] {p["name"].title()}{desc}\n'
            f'       Pool: {fmt_rp(p["pool"])} | Sisa: {fmt_rp(p["balance"])}'
        )
    return "\n".join(lines)


def fmt_bantuan():
    return (
        "🤖 Atur Uang — Perintah:\n"
        "   devi buat [nama project] [modal]\n"
        "   devi buat [nama] [modal] deskripsi [teks]\n"
        "   devi catat [project] [nominal] [keterangan]\n"
        "   devi saldo [project?]\n"
        "   devi laporan [project]\n"
        "   devi laporan [project] minggu ini\n"
        "   devi hapus [id transaksi]\n"
        "   devi list\n"
        "   devi bantuan\n\n"
        "💡 Nominal: 100jt, 2jt, 500rb, 1.5jt, 50000"
    )


def fmt_error(msg):
    return f"❌ {msg}"
