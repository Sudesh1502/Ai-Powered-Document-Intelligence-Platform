import sys

file_path = "app.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(189, 668):  # lines 190 to 668 (0-indexed)
    lines[i] = "    " + lines[i]

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)
