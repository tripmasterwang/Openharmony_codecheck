import pandas as pd
import json
import os

def excel_to_json(excel_path):
    # 读取Excel（默认第一行为标题）
    df = pd.read_excel(excel_path)

    # 增加行号列 index，从0始
    df.insert(0, "index", range(0, len(df)))

    # 转换为字典列表
    data = df.to_dict(orient='records')

    # 输出路径
    base, _ = os.path.splitext(excel_path)
    output_path = base + '.json'

    # 写入JSON文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"转换完成：{output_path}")

if __name__ == "__main__":
    excel_path = "dataset1/openharmony/test/vendor_telink/代码问题记录25-10-18-14-47-41.xlsx"
    excel_to_json(excel_path)
