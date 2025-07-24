import pandas as pd
import re


class DataLoader:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = self._load_excel()

    def _load_excel(self):
        df = pd.read_excel(self.data_path)
        return df

    def get_sku_from_title(self):
        # 列出多个正则规则，依次匹配，直到匹配出货号
        # 如果都没匹配到，则打印出问题的title
        # 如果 商品名称 在黑名单里，则删除这条记录
        black_list = ["Chanel/香奈儿蔚蓝男士淡香水EDT100ml 男士留香夏日魅力少年经典"]
        regex_rules = [
            r"美区大牌奢品-(.*?)-",
            r"美区大牌奢品-【款号(.*?)琪】",
        ]
        for index, row in self.df.iterrows():
            title = row["商品名称"]
            if title in black_list:
                self.df = self.df.drop(index)
                continue
            for rule in regex_rules:
                match = re.search(rule, title)
                if match:
                    sku = match.group(1)
                    self.df.at[index, "SKU"] = sku
                    break
            else:
                print(f"问题title: {title}")

    def clean_data(self):
        new_df = self.df.drop(
            columns=[
                "商品ID",
                "预售订单数",
                "商品曝光-点击率（人数）",
                "千次曝光用户支付金额",
                "发货前退款订单数",
                "发货前退款金额",
                "发货前退款人数",
                "发货前订单退款率",
                "发货后退款订单数",
                "发货后退款金额",
                "发货后退款人数",
                "发货后订单退款率",
            ]
        )
        self.df = new_df
        # convert 首次上架时间 to datetime. only keep Month and Day
        self.df["首次上架时间"] = pd.to_datetime(self.df["首次上架时间"]).dt.strftime(
            "%m-%d"
        )
        # convert 讲解次数 to int
        self.df["讲解次数"] = self.df["讲解次数"].astype(int)
        # clean 直播间价格, remove ¥ from 直播间价格, remove , from 直播间价格
        self.df["直播间价格"] = self.df["直播间价格"].str.replace("¥", "")
        self.df["直播间价格"] = self.df["直播间价格"].str.replace(",", "")
        # clean 用户支付金额, remove ¥ from 用户支付金额, remove , from 用户支付金额
        self.df["用户支付金额"] = self.df["用户支付金额"].str.replace("¥", "")
        self.df["用户支付金额"] = self.df["用户支付金额"].str.replace(",", "")
        # convert 商品点击人数 to int
        self.df["商品点击人数"] = self.df["商品点击人数"].astype(int)
        # convert 直播间价格 用户支付金额  to float
        self.df["直播间价格"] = self.df["直播间价格"].astype(float)
        self.df["用户支付金额"] = self.df["用户支付金额"].astype(float)
        # convert 商品点击-成交转化率（人数） to percent
        # remove % symbol and convert to float
        self.df["商品点击-成交转化率（人数）"] = (
            self.df["商品点击-成交转化率（人数）"].str.replace("%", "").astype(float)
        )
        # add column 成交件数/每次讲解
        self.df["成交件数/每次讲解"] = self.df["成交件数"] / self.df["讲解次数"]

        # remove 商品名称
        self.df = self.df.drop(columns=["商品名称"])
        # move SKU to the first column
        self.df = self.df[["SKU"] + [col for col in self.df.columns if col != "SKU"]]
