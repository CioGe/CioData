#!/usr/bin/env bash
# CioData 启动脚本（macOS / Linux）
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Install Python 3.12+ first."
    exit 1
fi

python3 launcher.py
