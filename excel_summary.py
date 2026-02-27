import pandas as pd


def main():
    # 路径指向项目目录下的 Excel 文件
    path = r"e:\GitHub\Website demo\CANGO\【汇总表】CANGO海外资源库-数据清洗 2026.02.27更新.xlsx"
    sheet_name = "合作机构 (DataWashing)"

    xls = pd.ExcelFile(path)
    print("Sheets:", xls.sheet_names)

    df = pd.read_excel(path, sheet_name=sheet_name)
    print("\nColumns:", list(df.columns))
    print("Shape:", df.shape)

    # 基本统计
    print("\n=== Summary ===")
    # 如果首列是编号，可以用它来识别真实数据行
    if "Unnamed: 0" in df.columns:
        num_col = pd.to_numeric(df["Unnamed: 0"], errors="coerce")
        data_df = df[num_col.notna()].copy()
    else:
        data_df = df

    print("原始行数（含说明行）:", len(df))
    print("机构数据行数:", len(data_df))

    # 粗略估计国家/地区列（根据样本观测第 7 列为中文国家）
    try:
        country_col = df.columns[6]
        print("国家/地区列名猜测:", country_col)
        print("覆盖国家/地区数:", data_df[country_col].nunique(dropna=True))

        # 同时按大洲/区域统计（第 6 列为区域：如“欧洲 (Europe)”）
        region_col = df.columns[5]
        print("区域列名猜测:", region_col)
        print("区域分布（前 10）:")
        print(data_df[region_col].value_counts(dropna=True).head(10))

        print("\n国家/地区分布（前 10）:")
        print(data_df[country_col].value_counts(dropna=True).head(10))
    except Exception as e:
        print("无法计算覆盖国家/地区数:", e)

    # 机构属性（类型/角色）与重点议题（主题领域）的粗略分布
    from collections import Counter

    def collect_counts(cols_idx):
        counter = Counter()
        for idx in cols_idx:
            if idx >= len(df.columns):
                continue
            col = df.columns[idx]
            vals = data_df[col].dropna().astype(str)
            for v in vals:
                v = v.strip()
                if not v:
                    continue
                counter[v] += 1
        return counter

    # 基于样本观察：13-15 列为机构属性/功能，16-18 列为主题议题
    type_counts = collect_counts([13, 14, 15])
    topic_counts = collect_counts([16, 17, 18])

    print("\n=== 机构属性/功能 Top 10（跨列 13-15 聚合）===")
    for text, cnt in type_counts.most_common(10):
        print(cnt, "x", text)

    print("\n=== 重点议题 Top 10（跨列 16-18 聚合）===")
    for text, cnt in topic_counts.most_common(10):
        print(cnt, "x", text)

    # 在华合作情况：通过包含 “Cooperation” 的英文标签识别
    print("\n=== 在华合作情况（含 Cooperation 的字段）===")
    coop_cols = []
    for col in df.columns:
        try:
            s = data_df[col].dropna().astype(str)
        except Exception:
            continue
        if s.str.contains("Cooperation", na=False).any():
            coop_cols.append(col)
    print("检测到的在华合作相关列：", coop_cols)
    for col in coop_cols:
        print(f"\n列 {col} 的值分布：")
        print(data_df[col].value_counts(dropna=True))

    # 打印首个机构在若干列的取值，辅助理解列含义
    print("\n=== 单行样本（编号为 1 的机构部分字段）===")
    try:
        row1 = data_df.iloc[0]
        # 打印从第 4 列到第 22 列，便于人工对照含义
        for idx in range(3, min(22, len(df.columns))):
            print(f"col{idx} = {df.columns[idx]} ->", row1.iloc[idx])
    except Exception as e:
        print("无法打印样本行:", e)

    # 尝试识别常见字段名，若不存在则跳过
    for col in ["国家/地区", "所在国家/地区", "country", "Country"]:
        if col in df.columns:
            print(f"覆盖国家/地区数 ({col}):", df[col].nunique(dropna=True))
            break

    for label, candidates in [
        ("机构类型", ["机构类型", "类型", "Type"]),
        ("主要职能", ["主要职能", "功能", "Function"]),
        ("关注议题", ["重点议题", "关注议题", "议题", "Topic"]),
        ("在华情况", ["在华情况", "中国合作情况"]),
        ("存续状态", ["存续状态", "Status", "机构状态"]),
    ]:
        for c in candidates:
            if c in df.columns:
                print(f"\n{label}（字段：{c}） value_counts 前 10：")
                print(df[c].value_counts(dropna=True).head(10))
                break

    print("\n=== Sample rows ===")
    try:
        from tabulate import tabulate

        print(tabulate(df.head(10), headers="keys", tablefmt="github", showindex=False))
    except Exception:
        print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

