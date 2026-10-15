"""CLI script to import validated synthetic datasets into Turso / SQLite.

Usage:
    python backend/scripts/import_dataset.py --data-dir backend/data/incoming [--replace-existing]
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.importer import import_source_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Import synthetic dataset into Turso database.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Path to directory containing source CSV files",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Explicitly allow replacement of existing synthetic dataset",
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="shivam_v1",
        help="Identifier for this dataset import (default: shivam_v1)",
    )

    args = parser.parse_args()
    data_dir: Path = args.data_dir

    print("=" * 70)
    print("ANVIK DATASET IMPORTER")
    print("=" * 70)
    print(f"Source Directory:  {data_dir.resolve()}")
    print(f"Dataset ID:        {args.dataset_id}")
    print(f"Replace Existing:  {args.replace_existing}")

    try:
        res = import_source_dataset(
            data_dir=data_dir,
            replace_existing=args.replace_existing,
            dataset_id=args.dataset_id,
        )

        print("\n--- IMPORT RESULTS ---")
        if res.is_noop:
            print("[STATUS] NO-OP (UNCHANGED)")
            print(f"  Message:         {res.message}")
            print(f"  Data Hash:       {res.data_hash}")
        else:
            print("[STATUS] SUCCESS")
            print(f"  Accounts:        {res.account_count:,}")
            print(f"  Devices:         {res.device_count:,}")
            print(f"  Account-Devices: {res.account_device_count:,}")
            print(f"  Transactions:    {res.transaction_count:,}")
            print(f"  Complaints:      {res.complaint_count:,}")
            print(f"  Data Hash:       {res.data_hash}")
            print(f"  Message:         {res.message}")

        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
