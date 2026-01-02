"""
CheXNet Weights Downloader

Instructions:
1. Download the weights manually from one of these sources:

   **Nasir6's CheXNet (Highest Accuracy - 87.79% AUROC):**
   https://github.com/nasir6/chexnet
   - Go to "Releases" or check the README for Google Drive link
   - Download: m-30012020-104001.pth.tar
   
   **Arnoweng's CheXNet (Well-tested - 84.7% AUROC):**
   https://github.com/arnoweng/CheXNet
   - Check README for Google Drive download link
   - Download: model.pth.tar

2. Rename the downloaded file to: chexnet_weights.pth.tar

3. Place it in this folder:
   radio_assistance/weights/chexnet_weights.pth.tar

Note: The weights file is typically 50-100 MB.
"""

import urllib.request
import os
from pathlib import Path

WEIGHTS_DIR = Path(__file__).parent

def check_weights():
    """Check if weights file exists."""
    weights_path = WEIGHTS_DIR / "chexnet_weights.pth.tar"
    if weights_path.exists():
        size_mb = weights_path.stat().st_size / (1024 * 1024)
        print(f"✓ Weights found: {weights_path}")
        print(f"  Size: {size_mb:.1f} MB")
        return True
    else:
        print("✗ Weights not found!")
        print(f"  Expected location: {weights_path}")
        print("\nPlease download from:")
        print("  https://github.com/arnoweng/CheXNet")
        print("  or")
        print("  https://github.com/nasir6/chexnet")
        return False

if __name__ == "__main__":
    check_weights()

