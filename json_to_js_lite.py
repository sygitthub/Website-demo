import json
from pathlib import Path


def normalize_region_std(row: dict) -> str:
  """根据标准化字段 + 文本推断总部所在大洲（简体中文标签）。"""
  region_std = str(row.get("总部所在区域_标准化") or "").strip()
  if region_std:
    return region_std

  raw = str(row.get("总部所在") or row.get("Unnamed: 11") or "").strip()

  # 先判断“中亚 / Central Asia”，避免被更泛化的“亚洲 / Asia”抢先匹配
  if "中亚" in raw or "Central Asia" in raw:
    return "中亚"
  if "欧洲" in raw or "Europe" in raw:
    return "欧洲"
  if "亚洲" in raw or "Asia" in raw:
    return "亚洲"
  if "北美" in raw or "North America" in raw:
    return "北美"
  if "南美" in raw or "拉美" in raw or "Latin America" in raw or "South America" in raw:
    return "南美/拉美"
  if "非洲" in raw or "Africa" in raw:
    return "非洲"
  if "大洋洲" in raw or "澳洲" in raw or "Oceania" in raw:
    return "大洋洲"
  if "中东" in raw or "Middle East" in raw:
    return "中东"

  return ""


def build_lite_payload() -> dict:
  src_path = Path("cango-global result.json")
  if not src_path.exists():
    raise FileNotFoundError(f"未找到 JSON 文件: {src_path}")

  data = json.loads(src_path.read_text(encoding="utf-8"))
  rows = data.get("机构总表", [])

  lite_orgs = []
  seen_names = set()

  for row in rows:
    name_std = str(
      row.get("机构名称_标准化") or row.get("机构名称") or ""
    ).strip()
    if not name_std:
      continue

    # 只按名称去重一次，避免页面重复显示
    if name_std in seen_names:
      continue
    seen_names.add(name_std)

    # 优先使用已在预处理脚本中生成的标准化区域字段，
    # 若为空再根据原始文本做一次兜底推断。
    region_std = str(row.get("总部所在区域_标准化") or "").strip()
    if not region_std:
      region_std = normalize_region_std(row)
    if not region_std:
      # 未能识别区域的机构暂不纳入按大洲展示
      continue

    raw_founded = row.get("成立时间")
    founded_str = "" if raw_founded is None else str(raw_founded).strip()
    try:
      founded_year = int(float(founded_str)) if founded_str else None
    except ValueError:
      founded_year = None

    nature_raw = str(
      row.get("机构性质\n（法律身份、本质属性）")
      or row.get("机构性质")
      or ""
    ).strip()
    nature_std = nature_raw.split("\n", 1)[0].strip() if nature_raw else ""

    function_raw = str(
      row.get("机构类型\n（职能定位、合作方式）") or ""
    ).strip()
    function_std = function_raw.split("\n", 1)[0].strip() if function_raw else ""

    raw_intro = str(
      row.get("机构业务及开展区域") or row.get("备注") or ""
    ).strip()
    intro = raw_intro
    if len(intro) > 200:
      intro = intro[:200] + "……"

    primary_region = str(
      row.get("总部所在") or row.get("Unnamed: 11") or region_std
    ).strip()

    subtitle_parts = []
    if founded_str:
      subtitle_parts.append(founded_str)
    if nature_raw:
      subtitle_parts.append(nature_raw)

    # 是否有分支机构（含境外 / 在华）
    has_branches = str(row.get("是否有分支机构") or "").strip() == "是"

    # 存续状态：含「正常运营」或「存续」视为正常运营，其余非空为需预警/待核查
    status_text = str(row.get("Unnamed: 29") or "").strip()
    if "正常运营" in status_text or "存续" in status_text:
      status_std = "Active"
      warning_reason = ""
    elif status_text:
      status_std = "Warning"
      # 精炼待核查原因：取首句或前 120 字，换行改为空格
      refined = status_text.replace("\n", " ").strip()
      if len(refined) > 120:
        refined = refined[:120].rstrip() + "…"
      warning_reason = refined
    else:
      status_std = ""
      warning_reason = ""

    lite_orgs.append(
      {
        "regionStd": region_std,
        "title": name_std,
        "subtitle": " ｜ ".join(subtitle_parts),
        "body": intro,
        "tag": primary_region,
        # 供统计使用的标准化字段
        "foundedYear": founded_year,
        "natureStd": nature_std,
        "functionStd": function_std,
        "hasBranches": has_branches,
        "statusStd": status_std,
        "warningReason": warning_reason,
      }
    )

  return {"orgs": lite_orgs}


def main() -> None:
  payload = build_lite_payload()
  out_path = Path("cango-data-lite.js")

  # 导出为简单的全局变量，便于在浏览器中直接使用
  with out_path.open("w", encoding="utf-8") as f:
    f.write("// 由 json_to_js_lite.py 自动生成，请勿手工编辑\n")
    f.write("window.CANGO_DATA = ")
    json.dump(payload, f, ensure_ascii=False)
    f.write(";\n")

  print(
    f"已生成 {out_path}，共 {len(payload['orgs'])} 家唯一机构（按名称去重且带区域信息）。"
  )


if __name__ == "__main__":
  main()

