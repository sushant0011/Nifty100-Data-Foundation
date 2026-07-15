import os
from pathlib import Path

pages_dir = Path("src/dashboard/pages")

for file in pages_dir.glob("*.py"):
    content = file.read_text(encoding="utf-8")
    
    # Fix sys.path
    old = "sys.path.append(str(Path(__file__).parent.parent))"
    new = "sys.path.append(str(Path(__file__).parent.parent.parent.parent))"
    
    content = content.replace(old, new)
    
    file.write_text(content, encoding="utf-8", newline="\n")
    print(f"Fixed: {file.name}")

print("All files fixed!")