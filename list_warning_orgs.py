# 临时脚本：列出「需预警/待核查」的机构名称（与看板存续状态分布统计口径一致）
import json
from pathlib import Path

path = Path("cango-global result.json")
data = json.loads(path.read_text(encoding="utf-8"))
rows = data.get("机构总表", [])

seen = set()
warning_names = []
for row in rows:
    name = str(row.get("机构名称_标准化") or row.get("机构名称") or "").strip()
    if not name or name in seen:
        continue
    seen.add(name)
    status_text = str(row.get("Unnamed: 29") or "").strip()
    # 与看板一致：含「正常运营」或「存续」为正常，其余非空为需预警
    if status_text and "正常运营" not in status_text and "存续" not in status_text:
        warning_names.append(name)

out = Path("warning_orgs_list.txt")
lines = [f"需预警/待核查 共 {len(warning_names)} 家："] + [f"{i}. {n}" for i, n in enumerate(warning_names, 1)]
out.write_text("\n".join(lines), encoding="utf-8")
print("已写入", out)
for line in lines:
    print(line)
