"""
列出当前被归入「其他」的机构性质、职能类型原始值及数量，便于判断是否可继续细分。

运行：在项目根目录执行
    python list_other_categories.py

依赖：需先存在 cango-global result.json（可由 rebuild_cango_from_excel 生成）。
      若使用 data.json / 前端 payload，则从 json_to_js_lite.build_lite_payload 取数据。
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

# 使用与 build_site_data 相同的归一化逻辑
from build_site_data import _normalize_nature, _normalize_function

try:
    from json_to_js_lite import build_lite_payload
except Exception:
    build_lite_payload = None


def main() -> None:
    if build_lite_payload is None:
        # 退路：直接读 data.json
        data_path = Path(__file__).resolve().parent / "data.json"
        if not data_path.exists():
            print("未找到 data.json，请先运行 build_site_data.py 或确保 cango-global result.json 存在后运行本脚本。")
            return
        payload = json.loads(data_path.read_text(encoding="utf-8"))
    else:
        payload = build_lite_payload()

    orgs = payload.get("orgs") or []
    print(f"共 {len(orgs)} 家机构\n")

    # 机构性质：被归为「其他」的原始值及数量
    nature_other: Counter[str] = Counter()
    nature_other_empty = 0
    for item in orgs:
        raw = str(item.get("natureStd") or "").strip()
        if _normalize_nature(raw) != "其他":
            continue
        if not raw:
            nature_other_empty += 1
        else:
            nature_other[raw] += 1

    print("=" * 60)
    print("机构性质分布 · 当前归入「其他」的原始值")
    print("=" * 60)
    print(f"  空值（未填）：{nature_other_empty} 家")
    for label, count in nature_other.most_common():
        print(f"  「{label}」：{count} 家")
    print(f"  小计（非空）：{sum(nature_other.values())} 家")
    print(f"  合计（其他）：{nature_other_empty + sum(nature_other.values())} 家\n")

    # 职能类型：被归为「其他」的原始值及数量
    func_other: Counter[str] = Counter()
    func_other_empty = 0
    for item in orgs:
        raw = str(item.get("functionStd") or "").strip()
        if _normalize_function(raw) != "其他":
            continue
        if not raw:
            func_other_empty += 1
        else:
            func_other[raw] += 1

    print("=" * 60)
    print("职能类型分布 · 当前归入「其他」的原始值")
    print("=" * 60)
    print(f"  空值（未填）：{func_other_empty} 家")
    for label, count in func_other.most_common():
        print(f"  「{label}」：{count} 家")
    print(f"  小计（非空）：{sum(func_other.values())} 家")
    print(f"  合计（其他）：{func_other_empty + sum(func_other.values())} 家")

    print("\n若上述非空原始值可归纳为新类别或并入现有类别，可在 build_site_data.py 的")
    print("_normalize_nature / _normalize_function 中增加关键词或规则后重新运行 build_site_data.py。")


if __name__ == "__main__":
    main()
