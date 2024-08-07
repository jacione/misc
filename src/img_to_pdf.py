import img2pdf
import sys
from pathlib import Path


if __name__ == "__main__":
    for img in sys.argv[1:]:
        img = Path(img)
        parent = img.parent.as_posix()
        name = img.stem
        with open(f"{parent}/{name}.pdf", "wb") as f:
            f.write(img2pdf.convert(f"{img.as_posix()}"))
