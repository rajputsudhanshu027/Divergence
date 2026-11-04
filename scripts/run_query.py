"""Run a named portfolio SQL query and print its result as CSV."""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

from retail_planner.analysis.export import SQL_DIR


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    queries = {path.stem: path for path in SQL_DIR.glob("*.sql")}
    parser.add_argument("query", choices=sorted(queries))
    parser.add_argument("--database", type=Path, default=Path("reports/latest/analysis.sqlite"))
    parser.add_argument("--limit", type=int, default=20, help="Maximum printed rows")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    if not args.database.is_file():
        parser.error("Database missing. Run: retail-planner analyze")
    # Open the database in read-only mode to prevent accidental writes.
    with sqlite3.connect(args.database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        cursor = connection.execute(queries[args.query].read_text(encoding="utf-8"))
        writer = csv.writer(sys.stdout)
        writer.writerow(field[0] for field in cursor.description)
        writer.writerows(cursor.fetchmany(args.limit))


if __name__ == "__main__":
    main()
