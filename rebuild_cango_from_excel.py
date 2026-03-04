import json
from pathlib import Path

import pandas as pd


def detect_header(xls: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    """在指定 sheet 中自动定位表头行，并返回带表头的 DataFrame。"""
    tmp = xls.parse(sheet, header=None)

    header_row_idx = None
    for i, row in tmp.head(40).iterrows():
        for v in row:
            if isinstance(v, str) and any(k in v for k in ("机构名称", "机构", "单位")):
                header_row_idx = i
                break
        if header_row_idx is not None:
            break

    if header_row_idx is None:
        raise RuntimeError("未能自动识别表头行（含 机构名称/机构/单位）")

    return xls.parse(sheet, header=header_row_idx)


def normalize_region_std(row: pd.Series) -> str:
    """根据 Excel 中的区域/描述文本推断标准化大洲名称（简体中文标签）。

    注意：不再信任原表中的「总部所在区域_标准化」旧值，而是完全基于当前规则重新推断，
    以避免历史标注错误（例如将中亚机构归为“亚洲”）被沿用。
    """
    # 兼容原始表头可能的写法，优先使用更语义化的字段
    # 优先使用更细粒度的字段，再退回到原来的“总部所在-区域”汇总字段
    candidates = [
        row.get("总部所在"),
        row.get("Unnamed: 12"),
        row.get("Unnamed: 11"),
        row.get("总部所在-区域"),
    ]
    raw = ""
    for c in candidates:
        if c:
            raw = str(c).strip()
            if raw:
                break

    if not raw:
        return ""

    # 先判断“中亚 / Central Asia”，避免被更泛化的“亚洲 / Asia”抢先匹配
    if "中亚" in raw or "Central Asia" in raw:
        return "中亚"
    if "欧洲" in raw or "Europe" in raw:
        return "欧洲"
    if "亚洲" in raw or "Asia" in raw:
        return "亚洲"
    if "北美" in raw or "North America" in raw:
        return "北美"
    if "南美" in raw or "Latin America" in raw or "South America" in raw or "拉美" in raw:
        return "南美/拉美"
    if "非洲" in raw or "Africa" in raw:
        return "非洲"
    if "大洋洲" in raw or "澳洲" in raw or "Oceania" in raw:
        return "大洋洲"
    if "中东" in raw or "Middle East" in raw:
        return "中东"

    return ""


def main() -> None:
    excel_path = Path("【汇总表】CANGO海外资源库-数据清洗 2026.03 更新.xlsx")
    if not excel_path.exists():
        raise FileNotFoundError(f"未找到 Excel 文件: {excel_path}")

    xls = pd.ExcelFile(excel_path)

    # 只使用 “CANGO海外资源库” 这个工作表
    sheet_name = None
    for s in xls.sheet_names:
        if "CANGO" in s and "海外" in s:
            sheet_name = s
            break

    if sheet_name is None:
        raise RuntimeError("未找到名为 CANGO海外资源库 的工作表")

    df = detect_header(xls, sheet_name)

    # 标准化机构名称字段
    name_col = None
    for c in df.columns:
        text = str(c)
        if "机构名称_标准化" in text:
            name_col = c
            break
    if name_col is None:
        for c in df.columns:
            text = str(c)
            if any(k in text for k in ("机构名称", "机构", "单位")):
                name_col = c
                break
    if name_col is None:
        raise RuntimeError("未能识别机构名称列")

    names = (
        df[name_col]
        .astype(str)
        .str.replace("\u3000", "", regex=False)
        .str.strip()
    )

    df["机构名称_标准化"] = names

    # 计算标准化区域
    df["总部所在区域_标准化"] = df.apply(normalize_region_std, axis=1)

    # 只保留名称与区域都有值的记录
    valid_mask = df["机构名称_标准化"].ne("") & df["总部所在区域_标准化"].ne("")
    df_valid = df.loc[valid_mask].copy()

    # 基于机构名称去重（以首次出现为准）
    before = len(df_valid)
    df_unique = df_valid.drop_duplicates(subset=["机构名称_标准化"]).copy()
    after = len(df_unique)

    # 导出为新的 Excel（便于人工核对）
    out_xlsx = Path("cango-global result.xlsx")
    df_unique.to_excel(out_xlsx, index=False)

    # 导出为 JSON，结构与现有前端脚本兼容
    records = df_unique.to_dict(orient="records")
    out_json = Path("cango-global result.json")
    with out_json.open("w", encoding="utf-8") as f:
        json.dump({"机构总表": records}, f, ensure_ascii=False, indent=2)

    print(f"原始记录（含无效行）: {len(df)}")
    print(f"有效记录（有名称+区域）: {before}")
    print(f"唯一机构数（按名称去重）: {after}")
    print(f"已写入: {out_xlsx} 与 {out_json}")


if __name__ == "__main__":
    main()

