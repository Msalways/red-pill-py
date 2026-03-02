import os
import shutil
from pathlib import Path
from setuptools.build_meta import build_meta as _build_meta

def copy_readme(build_dir, config_settings):
    src = Path(__file__).parent.parent / "README.md"
    dst = Path(__file__).parent / "README.md"
    if src.exists():
        shutil.copy2(src, dst)
        print(f"Copied README.md to {dst}")

class build_meta(_build_meta):
    def run(self):
        copy_readme(None, None)
        super().run()
