import os
from utils import DataLoader, logger


def main():
    sku_name_list = []
    # 遍历data/目录下的所有xlsx文件
    for file in os.listdir("data"):
        if file.endswith(".xlsx"):
            data_loader = DataLoader(f"data/{file}")
            for session_data in data_loader.session_data.values():
                for index, row in session_data.iterrows():
                    # get 商品名称 from row
                    sku_name = row["商品名称"]
                    # save name to file
                    sku_name_list.append(sku_name)
                break

    # 去重
    sku_name_list = list(set(sku_name_list))
    # 排序
    sku_name_list.sort()
    # 写入文件
    with open(f"sku_name.txt", "w") as f:
        for sku_name in sku_name_list:
            f.write(sku_name + "\n")


if __name__ == "__main__":
    main()
