"""
bootstrap_schema — tạo 22 bảng nền (legacy) của ProgrammingEdu trên DB hiện tại
từ sql/legacy_schema.sql. Dùng khi dựng một NeonDB mới từ đầu (vd bản HSA).

- Idempotent: mọi statement dùng CREATE ... IF NOT EXISTS.
- KHÔNG seed nội dung (seed HSA nằm ở lệnh seed_data).
- Các bảng để managed=False trong Django → migrate không đụng tới; lệnh này là
  nguồn DDL duy nhất cho chúng.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


def _split_statements(raw: str):
    # Bỏ comment dòng ('--' đến hết dòng) TRƯỚC — vì comment có thể chứa ';'
    # (không statement/string DDL nào chứa '--' hay ';'), rồi mới tách theo ';'.
    stripped = []
    for line in raw.splitlines():
        idx = line.find("--")
        if idx != -1:
            line = line[:idx]
        stripped.append(line)
    cleaned = "\n".join(stripped)
    return [s.strip() for s in cleaned.split(";") if s.strip()]


class Command(BaseCommand):
    help = "Tạo 22 bảng nền (legacy) từ sql/legacy_schema.sql. Idempotent."

    def _count_tables(self, cur):
        cur.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_type='BASE TABLE'"
        )
        return cur.fetchone()[0]

    def handle(self, *args, **options):
        sql_dir = Path(settings.BASE_DIR) / "sql"
        sql_files = sorted(sql_dir.glob("*.sql"))   # legacy_schema.sql trước mockexam_schema.sql
        if not sql_files:
            self.stderr.write(f"Không thấy file .sql nào trong: {sql_dir}")
            return

        total = 0
        with connection.cursor() as cur:
            before = self._count_tables(cur)
            for sql_path in sql_files:
                statements = _split_statements(sql_path.read_text(encoding="utf-8"))
                for i, stmt in enumerate(statements, 1):
                    try:
                        cur.execute(stmt)
                    except Exception as exc:
                        head = stmt.splitlines()[0][:80]
                        self.stderr.write(f"[{sql_path.name} stmt #{i}] LỖI ở: {head}\n  -> {exc}")
                        raise
                total += len(statements)
                self.stdout.write(f"  · {sql_path.name}: {len(statements)} statements")
            after = self._count_tables(cur)

        self.stdout.write(self.style.SUCCESS(
            f"[bootstrap_schema] public base tables: {before} -> {after} ({total} statements OK)"
        ))
