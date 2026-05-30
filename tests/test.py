# tests/test.py
from __future__ import annotations

import subprocess
from pathlib import Path
from datetime import datetime


def main():
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "tests"
    out_dir.mkdir(exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = out_dir / f"test_results_{ts}.txt"

    cmd = ["pytest", "-q", str(out_dir)]

    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)

    content = []
    content.append("=== PYTEST RESULTS ===\n")
    content.append(f"Command: {' '.join(cmd)}\n\n")
    content.append("=== STDOUT ===\n")
    content.append(proc.stdout + "\n")
    content.append("=== STDERR ===\n")
    content.append(proc.stderr + "\n")
    content.append(f"Exit code: {proc.returncode}\n")

    report_path.write_text("".join(content), encoding="utf-8")
    print(f"Saved test report: {report_path}")

    # Make exit code reflect test status
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()

