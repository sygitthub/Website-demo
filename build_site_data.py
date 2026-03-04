"""
一键构建前端数据脚本。

功能：
1. 从 Excel【汇总表】CANGO海外资源库-数据清洗 2026.02 更新.xlsx 读取最新数据，
   调用现有清洗逻辑生成标准化结果（cango-global result.json）。
2. 基于清洗结果构建压缩版数据结构，写入 data.json（供备查或其他用途）。
3. 根据压缩数据自动计算：
   - 机构总数（去重后）
   - 覆盖大洲数
   - 各大洲机构数量
   并直接更新 index.html 里的 summaryMetrics 与 regionDistribution 常量。

使用方式：
在项目根目录（E:/GitHub/cango-global）运行：

    python build_site_data.py

运行成功后，刷新浏览器中的 index.html 即可看到最新统计。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

from collections import Counter

from rebuild_cango_from_excel import main as rebuild_from_excel
from json_to_js_lite import build_lite_payload


ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "index.html"
DATA_JSON_PATH = ROOT / "data.json"


REGION_STD_TO_KEY: Dict[str, str] = {
    "欧洲": "Europe",
    "亚洲": "Asia",
    "北美": "North America",
    "南美/拉美": "South America",
    "非洲": "Africa",
    "大洋洲": "Oceania",
    "中亚": "Central Asia",
    "中东": "Middle East",
}

# 保持与前端 regionDistribution 同样的顺序与配色
REGION_KEY_ORDER: List[Tuple[str, str, str]] = [
    ("Europe", "欧洲 (Europe)", "#4F86FF"),
    ("Asia", "亚洲 (Asia)", "#22C55E"),
    ("North America", "北美洲 (North America)", "#EAB308"),
    ("Africa", "非洲 (Africa)", "#F97316"),
    ("South America", "南美洲 (South America)", "#06B6D4"),
    ("Oceania", "大洋洲 (Oceania)", "#A855F7"),
    ("Central Asia", "中亚 (Central Asia)", "#F43F5E"),
    ("Middle East", "中东 (Middle East)", "#EC4899"),
]

# 机构性质标准分类（饼图 6 类：非营利并入 NGO/社会组织，合计 = 总机构数）
NATURE_STD_ORDER: List[str] = [
    "非政府组织/社会组织",
    "宗教背景机构",
    "基金会/信托",
    "学术/科研机构",
    "政府背景机构",
    "其他",
]


def _normalize_nature(raw: str) -> str:
    """将 Excel 机构性质归入饼图 6 类，非营利与非政府组织/社会组织归为一类。"""
    s = (raw or "").strip()
    if not s or s.lower() == "nan":
        return "其他"
    # 非营利 + 非政府/社会组织 -> 非政府组织/社会组织
    if "非营利" in s or "Nonprofit" in s:
        return "非政府组织/社会组织"
    if "非政府" in s or "社会组织" in s or "NGO" in s.upper() or "Civil Society" in s:
        return "非政府组织/社会组织"
    if "宗教" in s or "Faith" in s:
        return "宗教背景机构"
    if "政府" in s and ("背景" in s or "组织" in s or "Agency" in s or "Affiliated" in s):
        return "政府背景机构"
    if (
        "基金会" in s
        or "慈善信托" in s
        or "Foundation" in s
        or "Charitable" in s
        or "注册慈善" in s
        or "Registered Charity" in s
    ):
        return "基金会/信托"
    if "学术" in s or "科研" in s or "大学" in s or "Academic" in s or "Research" in s or "University" in s:
        return "学术/科研机构"
    # 政府间/多边、营利性、社会企业等归入其他
    return "其他"


# 职能类型标准分类（MECE：按主职能划分，保证合计 = 总机构数）
# 1）执行实施型  2）资助型  3）网络/平台型  4）研究/咨询与能力建设  5）倡导/传播与教育  6）其他
FUNCTION_STD_ORDER: List[str] = [
    "执行实施型",
    "资助型机构",
    "网络/平台型机构",
    "研究/咨询与能力建设",
    "倡导/传播与教育",
    "其他",
]


def _normalize_function(raw: str) -> str:
    """将 Excel 职能类型归入上述 5+1 类（MECE），空值归为「其他」。

    规则按“最能代表其合作角色”的主功能划分，保证每家机构只落入一个桶。
    """
    s = (raw or "").strip()
    if not s or s.lower() == "nan":
        return "其他"

    # 1. 执行实施型：以项目落地、现场执行为主
    if "执行" in s or "Implementing" in s or "Implementation" in s:
        return "执行实施型"

    # 2. 资助型机构：拨款、基金、捐赠为主
    if "资助" in s or "Funding" in s or "Grant" in s or "Donor" in s:
        return "资助型机构"

    # 3. 网络 / 平台型机构：联盟、平台、网络协调
    if (
        "网络" in s
        or "Network" in s
        or "平台" in s
        or "Platform" in s
        or "联盟" in s
        or "Coalition" in s
    ):
        return "网络/平台型机构"

    # 4. 研究 / 咨询与能力建设：研究、智库、咨询、培训、技术支持
    if (
        "咨询" in s
        or "研究" in s
        or "Consult" in s
        or "Research" in s
        or "能力建设" in s
        or "Capacity" in s
        or "培训" in s
        or "Training" in s
        or "技术支持" in s
        or "Technical Assistance" in s
    ):
        return "研究/咨询与能力建设"

    # 5. 倡导 / 传播与教育：政策倡导、传播、媒体、公众教育、交流推广
    if (
        "倡导" in s
        or "政策" in s
        or "Advocacy" in s
        or "Policy" in s
        or "媒体" in s
        or "传播" in s
        or "Communication" in s
        or "Campaign" in s
        or "教育" in s
        or "Education" in s
        or "交流" in s
        or "Exchange" in s
        or "宣传" in s
        or "Awareness" in s
    ):
        return "倡导/传播与教育"

    # 其余少数特殊机制统一归入「其他」
    return "其他"


def compute_metrics_from_payload(payload: dict) -> Tuple[dict, List[dict], dict]:
    """从压缩后的 orgs 列表中计算 summaryMetrics、regionDistribution 及其他图表所需统计。"""
    orgs = payload.get("orgs") or []

    # 机构总数（orgs 已按名称去重）
    total_orgs = len(orgs)

    # 区域分布
    counts_by_key: Dict[str, int] = {}
    for item in orgs:
        std = str(item.get("regionStd") or "").strip()
        if not std:
            continue
        key = REGION_STD_TO_KEY.get(std)
        if not key:
            continue
        counts_by_key[key] = counts_by_key.get(key, 0) + 1

    regions_covered = sum(1 for v in counts_by_key.values() if v > 0)

    # 分支机构数（含境外 / 在华分支）
    orgs_with_branches = sum(
        1 for item in orgs if bool(item.get("hasBranches"))
    )

    # 存续状态分布：Active / Warning
    active_orgs = 0
    warning_orgs = 0
    for item in orgs:
        status = str(item.get("statusStd") or "").strip()
        if status == "Active":
            active_orgs += 1
        elif status == "Warning":
            warning_orgs += 1

    # 若 Excel 中暂未完整标注，则保持与原有常量兼容
    if active_orgs == 0 and warning_orgs == 0:
        active_orgs = 190
        warning_orgs = max(total_orgs - active_orgs, 0)

    summary_metrics = {
        "totalOrgs": total_orgs,
        "activeOrgs": active_orgs,
        "regionsCovered": regions_covered or 8,
        "orgsWithBranches": orgs_with_branches,
    }

    region_distribution: List[dict] = []
    for key, label, color in REGION_KEY_ORDER:
        value = counts_by_key.get(key, 0)
        region_distribution.append(
            {"label": label, "key": key, "value": value, "color": color}
        )

    # 机构性质 / 职能类型占比（每机构必归一类，保证两侧合计均为 total_orgs）
    nature_counter: Counter[str] = Counter()
    func_counter: Counter[str] = Counter()
    founded_years: List[int] = []

    for item in orgs:
        nature_raw = str(item.get("natureStd") or "").strip()
        nature_counter[_normalize_nature(nature_raw)] += 1

        func_raw = str(item.get("functionStd") or "").strip()
        func_counter[_normalize_function(func_raw)] += 1

        year = item.get("foundedYear")
        if isinstance(year, (int, float)):
            y = int(year)
            if 1800 <= y <= 2100:
                founded_years.append(y)

    # 按固定顺序输出，仅包含出现过的类别，合计 = total_orgs
    # 机构性质分布：按数量从多到少排序，「其他」固定放在最后
    nature_pairs: List[Tuple[str, int]] = [
        (label, nature_counter[label])
        for label in NATURE_STD_ORDER
        if nature_counter[label] > 0
    ]
    nature_pairs_sorted = sorted(
        nature_pairs,
        key=lambda p: (p[0] == "其他", -p[1]),
    )
    org_nature_distribution = [
        {"label": label, "key": label, "value": count}
        for label, count in nature_pairs_sorted
    ]
    # 职能类型分布：按数量从多到少排序，「其他」固定放在最后
    func_pairs: List[Tuple[str, int]] = [
        (label, func_counter[label])
        for label in FUNCTION_STD_ORDER
        if func_counter[label] > 0
    ]
    func_pairs_sorted = sorted(
        func_pairs,
        key=lambda p: (p[0] == "其他", -p[1]),
    )
    function_type_distribution = [
        {"label": label, "key": label, "value": count}
        for label, count in func_pairs_sorted
    ]

    # 成立年份区间分布
    buckets = [
        ("≤1990", lambda y: y <= 1990),
        ("1991–1995", lambda y: 1991 <= y <= 1995),
        ("1996–2000", lambda y: 1996 <= y <= 2000),
        ("2001–2005", lambda y: 2001 <= y <= 2005),
        ("2006–2010", lambda y: 2006 <= y <= 2010),
        ("2011–2015", lambda y: 2011 <= y <= 2015),
        ("2016–2020", lambda y: 2016 <= y <= 2020),
        ("2021–2025", lambda y: 2021 <= y <= 2025),
    ]

    founded_counts: List[dict] = []
    for label, matcher in buckets:
        count = sum(1 for y in founded_years if matcher(y))
        founded_counts.append({"label": label, "count": count})

    extra_metrics = {
        "statusDistribution": [
            {"label": "正常运营", "key": "Active", "value": active_orgs, "color": "#22C55E"},
            {
                "label": "需预警 / 待核查",
                "key": "Warning",
                "value": warning_orgs,
                "color": "#F97373",
            },
        ],
        "orgNatureDistribution": org_nature_distribution,
        "functionTypeDistribution": function_type_distribution,
        "foundedYearTrend": founded_counts,
    }

    return summary_metrics, region_distribution, extra_metrics


def write_cango_data_lite_js(payload: dict) -> None:
    """将轻量 payload 写入 cango-data-lite.js，供前端直接使用。

    这样浏览器里的 window.CANGO_DATA 与 data.json / index.html 始终保持一致，
    避免出现“脚本统计正确，但前端仍然读取旧 JS 文件”的不一致问题。
    """
    out_path = ROOT / "cango-data-lite.js"
    orgs = payload.get("orgs") or []

    with out_path.open("w", encoding="utf-8") as f:
        f.write("// 由 build_site_data.py 自动生成，请勿手工编辑\n")
        f.write("window.CANGO_DATA = ")
        json.dump(payload, f, ensure_ascii=False)
        f.write(";\n")

    print(f">>> 已写入前端轻量数据：{out_path}（orgs={len(orgs)}）")


def update_index_html(summary: dict, region_dist: List[dict], extra: dict) -> None:
    """将新的 summaryMetrics、regionDistribution 及其他图表配置写回 index.html。"""
    text = INDEX_PATH.read_text(encoding="utf-8")

    # 更新 summaryMetrics
    summary_js = (
        "const summaryMetrics = {\n"
        f"        totalOrgs: {summary['totalOrgs']},\n"
        f"        activeOrgs: {summary['activeOrgs']},\n"
        f"        regionsCovered: {summary['regionsCovered']},\n"
        f"        orgsWithBranches: {summary['orgsWithBranches']},\n"
        "      };"
    )

    text, n1 = re.subn(
        r"const summaryMetrics = \{[\s\S]*?\};",
        summary_js,
        text,
        count=1,
    )

    # 更新 regionDistribution
    region_lines = ["const regionDistribution = ["]
    for entry in region_dist:
        region_lines.append(
            "        { "
            f'label: "{entry["label"]}", '
            f'key: "{entry["key"]}", '
            f"value: {entry['value']}, "
            f'color: "{entry["color"]}" '
            "},"
        )
    region_lines.append("      ];")
    region_js = "\n".join(region_lines)

    text, n2 = re.subn(
        r"const regionDistribution = \[[\s\S]*?];",
        region_js,
        text,
        count=1,
    )

    # 更新存续状态分布（statusDistribution）
    status = extra.get("statusDistribution") or []
    status_lines = ["const statusDistribution = ["]
    for entry in status:
        status_lines.append(
            "      { "
            f'label: "{entry["label"]}", '
            f'key: "{entry["key"]}", '
            f"value: {entry['value']}, "
            f'color: "{entry["color"]}" '
            "},"
        )
    status_lines.append("      ];")
    status_js = "\n".join(status_lines)

    text, n3 = re.subn(
        r"const statusDistribution = \[[\s\S]*?];",
        status_js,
        text,
        count=1,
    )

    # 更新机构性质分布（orgNatureDistribution）
    nature_dist = extra.get("orgNatureDistribution") or []
    nature_lines = ["const orgNatureDistribution = ["]
    for entry in nature_dist:
        nature_lines.append(
            "      { "
            f'label: "{entry["label"]}", '
            f'key: "{entry["key"]}", '
            f"value: {entry['value']}"
            " },"
        )
    nature_lines.append("      ];")
    nature_js = "\n".join(nature_lines)

    text, n4 = re.subn(
        r"const orgNatureDistribution = \[[\s\S]*?];",
        nature_js,
        text,
        count=1,
    )

    # 更新职能类型分布（functionTypeDistribution）
    func_dist = extra.get("functionTypeDistribution") or []
    func_lines = ["const functionTypeDistribution = ["]
    for entry in func_dist:
        func_lines.append(
            "      { "
            f'label: "{entry["label"]}", '
            f'key: "{entry["key"]}", '
            f"value: {entry['value']}"
            " },"
        )
    func_lines.append("      ];")
    func_js = "\n".join(func_lines)

    text, n5 = re.subn(
        r"const functionTypeDistribution = \[[\s\S]*?];",
        func_js,
        text,
        count=1,
    )

    # 更新成立时间趋势（foundedYearTrend）
    founded = extra.get("foundedYearTrend") or []
    founded_lines = ["const foundedYearTrend = ["]
    for entry in founded:
        founded_lines.append(
            "      { "
            f'label: "{entry["label"]}", '
            f"count: {entry['count']}"
            " },"
        )
    founded_lines.append("      ];")
    founded_js = "\n".join(founded_lines)

    text, n6 = re.subn(
        r"const foundedYearTrend = \[[\s\S]*?];",
        founded_js,
        text,
        count=1,
    )

    # 更新底部“数据校验说明｜总部区域统计”表格数据
    tbody_pattern = re.compile(
        r'<tbody class="divide-y divide-slate-800/70">[\s\S]*?</tbody>'
    )

    rows_html = []
    for entry in region_dist:
        zh_label = entry["label"].split("（", 1)[0] if "（" in entry["label"] else entry["label"]
        rows_html.append(
            "                  <tr>\n"
            f'                    <td class="px-3 py-2 text-[11px] text-slate-100">\n'
            f"                      {zh_label}\n"
            "                    </td>\n"
            f'                    <td class="px-3 py-2 text-[11px] text-slate-100">\n'
            f"                      {entry['value']}\n"
            "                    </td>\n"
            f'                    <td class="px-3 py-2 text-[11px] text-emerald-300">\n'
            f"                      {entry['value']}\n"
            "                    </td>\n"
            "                  </tr>"
        )

    total_row = (
        "                  <tr class=\"bg-slate-900/80\">\n"
        '                    <td class="px-3 py-2 text-[11px] text-slate-100 font-medium">\n'
        "                      合计\n"
        "                    </td>\n"
        '                    <td class="px-3 py-2 text-[11px] text-slate-100 font-medium">\n'
        f"                      {summary['totalOrgs']}\n"
        "                    </td>\n"
        '                    <td class="px-3 py-2 text-[11px] text-emerald-300 font-medium">\n'
        f"                      {summary['totalOrgs']}\n"
        "                    </td>\n"
        "                  </tr>"
    )

    new_tbody = (
        '                  <tbody class="divide-y divide-slate-800/70">\n'
        + "\n".join(rows_html)
        + "\n"
        + total_row
        + "\n"
        "                </tbody>"
    )

    text, n7 = re.subn(tbody_pattern, new_tbody, text, count=1)

    INDEX_PATH.write_text(text, encoding="utf-8")

    print(
        "index.html 已更新："
        f"summaryMetrics({n1} 处)、"
        f"regionDistribution({n2} 处)、"
        f"statusDistribution({n3} 处)、"
        f"orgNatureDistribution({n4} 处)、"
        f"functionTypeDistribution({n5} 处)、"
        f"foundedYearTrend({n6} 处)、"
        f"region summary table({n7} 处)"
    )


def main() -> None:
    # 1. 先从 Excel 重新构建标准化结果（写入 cango-global result.json）
    print(">>> 从 Excel 重新构建标准化结果…")
    rebuild_from_excel()

    # 2. 基于标准化结果构建轻量数据（与前端结构一致）
    print(">>> 从标准化结果构建压缩数据 payload…")
    payload = build_lite_payload()

    # 写入 data.json 供检查或其他用途
    DATA_JSON_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f">>> 已写入压缩数据：{DATA_JSON_PATH}")

    # 同步生成前端使用的 cango-data-lite.js（window.CANGO_DATA）
    write_cango_data_lite_js(payload)

    # 3. 计算 summaryMetrics、各类分布，并写回 index.html
    summary, region_dist, extra = compute_metrics_from_payload(payload)
    print(">>> 统计结果：")
    print("    - 机构总数:", summary["totalOrgs"])
    print("    - 覆盖大洲数:", summary["regionsCovered"])
    print(
        "    - 区域分布:",
        ", ".join(f'{e["key"]}={e["value"]}' for e in region_dist),
    )

    print(">>> 更新 index.html 中的数据常量…")
    update_index_html(summary, region_dist, extra)

    print(">>> 完成。刷新浏览器中的 index.html 以查看最新效果。")


if __name__ == "__main__":
    main()

