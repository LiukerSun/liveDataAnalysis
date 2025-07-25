import pandas as pd
import re
import os
from pathlib import Path
from utils import logger


class DataLoader:
    def __init__(self, data_path):
        """
        初始化数据加载器
        data_path: 可以是单个文件路径、文件列表或包含excel文件的文件夹路径
        """
        self.data_path = data_path
        self.session_data = {}  # 存储每场的数据
        self.df = None  # 合并后的数据
        self.aggregated_df = None  # 聚合后的数据
        self._load_data()

    def _load_data(self):
        """根据输入类型加载数据"""
        if isinstance(self.data_path, str):
            if os.path.isdir(self.data_path):
                # 文件夹路径，加载文件夹中所有xlsx文件
                self._load_from_directory(self.data_path)
            elif os.path.isfile(self.data_path):
                # 单个文件路径
                self._load_single_file(self.data_path)
            else:
                raise FileNotFoundError(f"路径不存在: {self.data_path}")
        elif isinstance(self.data_path, list):
            # 文件列表
            self._load_from_file_list(self.data_path)
        else:
            raise ValueError("data_path必须是文件路径、文件列表或文件夹路径")

    def _load_from_directory(self, directory_path):
        """从文件夹加载所有xlsx文件"""
        xlsx_files = list(Path(directory_path).glob("*.xlsx"))
        if not xlsx_files:
            raise FileNotFoundError(f"文件夹 {directory_path} 中没有找到xlsx文件")

        for file_path in xlsx_files:
            session_name = file_path.stem  # 使用文件名（不含扩展名）作为场次名
            self._load_session_file(str(file_path), session_name)

    def _load_from_file_list(self, file_list):
        """从文件列表加载数据"""
        for i, file_path in enumerate(file_list):
            if not os.path.isfile(file_path):
                logger.error(f"警告：文件不存在，跳过: {file_path}")
                continue
            session_name = f"第{i+1}场"
            if isinstance(file_path, str) and file_path.endswith(".xlsx"):
                # 如果文件名包含日期等信息，可以提取作为场次名
                file_name = Path(file_path).stem
                session_name = file_name
            self._load_session_file(file_path, session_name)

    def _load_single_file(self, file_path):
        """加载单个文件"""
        session_name = Path(file_path).stem
        self._load_session_file(file_path, session_name)

    def _load_session_file(self, file_path, session_name):
        """加载单个场次的文件"""
        try:
            df = pd.read_excel(file_path)
            df["场次"] = session_name
            self.session_data[session_name] = df
            logger.info(f"已加载场次: {session_name}, 数据条数: {len(df)}")
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}")

    def get_sku_from_title(self):
        """为所有场次的数据提取SKU"""
        black_list = [
            "Chanel/香奈儿蔚蓝男士淡香水EDT100ml 男士留香夏日魅力少年经典",
            "拉布布POPMART泡泡玛特三代搪胶脸毛绒公仔玩具可爱盲盒",
            "HELMER复古圆框墨镜女网红金属小框太阳镜韩版时尚遮阳眼镜男3381",
        ]
        regex_rules = [
            # 主要模式：美区[前缀]-货号
            r"美区[^-]*-([A-Z]*\d+[A-Z#]*|\d+[A-Z#]*|[A-Z]+\d+)",
            # 【款号XXX琪】格式
            r"【款号([A-Z]*\d+[A-Z]*|\d+[A-Z]*|[A-Z]+\d+)琪】",
            # 多层级格式：美区大牌奢品-描述-描述-货号
            r"美区[^-]*-.*?-.*?-([A-Z]*\d+[A-Z]*|\d+[A-Z]*|[A-Z]+\d+)",
            # 通用模式：-货号（作为后备）
            r"-([A-Z]\d+|\d+[A-Z]?|\d+)(?:[^A-Z\d]|$|#)",
            # 【TX】货号格式
            r"【[A-Z]+】([A-Z]*\d+[A-Z]*|\d+[A-Z]*|[A-Z]+\d+)",
            # 纯货号格式（如DC007）
            r"([A-Z]+\d+)(?:\s|$)",
        ]

        for session_name, df in self.session_data.items():
            for index, row in df.iterrows():
                title = row["商品名称"]
                if title in black_list:
                    self.session_data[session_name] = self.session_data[
                        session_name
                    ].drop(index)
                    continue
                for rule in regex_rules:
                    match = re.search(rule, title)
                    if match:
                        sku = match.group(1)
                        self.session_data[session_name].at[index, "SKU"] = sku
                        break
                else:
                    logger.error(f"场次 {session_name} 问题title: {title}")

    def clean_data(self):
        """清理所有场次的数据"""
        for session_name, df in self.session_data.items():
            cleaned_df = self._clean_single_dataframe(df)
            self.session_data[session_name] = cleaned_df

        # 合并所有场次的数据
        if self.session_data:
            self.df = pd.concat(self.session_data.values(), ignore_index=True)

    def _clean_single_dataframe(self, df):
        """清理单个数据框"""
        # 删除不需要的列
        columns_to_drop = [
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

        # 只删除存在的列
        existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]
        new_df = df.drop(columns=existing_columns_to_drop)

        # 处理时间格式
        if "首次上架时间" in new_df.columns:
            new_df["首次上架时间"] = pd.to_datetime(new_df["首次上架时间"]).dt.strftime(
                "%m-%d"
            )

        # 处理数值列
        if "讲解次数" in new_df.columns:
            new_df["讲解次数"] = new_df["讲解次数"].astype(int)

        # 清理价格列
        if "直播间价格" in new_df.columns:
            new_df["直播间价格"] = (
                new_df["直播间价格"]
                .str.replace("¥", "")
                .str.replace(",", "")
                .astype(float)
            )

        if "用户支付金额" in new_df.columns:
            new_df["用户支付金额"] = (
                new_df["用户支付金额"]
                .str.replace("¥", "")
                .str.replace(",", "")
                .astype(float)
            )

        # 处理其他数值列
        if "商品点击人数" in new_df.columns:
            new_df["商品点击人数"] = new_df["商品点击人数"].astype(int)

        # 处理转化率
        if "商品点击-成交转化率（人数）" in new_df.columns:
            new_df["商品点击-成交转化率（人数）"] = (
                new_df["商品点击-成交转化率（人数）"].str.replace("%", "").astype(float)
            )

        # 计算讲解效率
        if "成交件数" in new_df.columns and "讲解次数" in new_df.columns:
            new_df["成交件数/每次讲解"] = (new_df["成交件数"] / new_df["讲解次数"]).round(2)

        # 计算单次讲解成交金额
        if "用户支付金额" in new_df.columns and "讲解次数" in new_df.columns:
            # 避免除零错误
            mask = new_df["讲解次数"] > 0
            new_df.loc[mask, "单次讲解成交金额"] = (new_df.loc[mask, "用户支付金额"] / new_df.loc[mask, "讲解次数"]).round(2)
            new_df.loc[~mask, "单次讲解成交金额"] = 0

        # 删除商品名称列
        if "商品名称" in new_df.columns:
            new_df = new_df.drop(columns=["商品名称"])

        # 重新排列列顺序，将SKU和场次放在前面
        cols = new_df.columns.tolist()
        priority_cols = ["SKU", "场次"]
        reordered_cols = [col for col in priority_cols if col in cols] + [
            col for col in cols if col not in priority_cols
        ]
        new_df = new_df[reordered_cols]

        return new_df

    def aggregate_by_sku(self):
        """按SKU聚合数据，对数值列求和，对其他列保留第一个值"""
        if self.df is None or self.df.empty:
            logger.error("警告：没有数据可以聚合")
            return

        # 定义需要求和的数值列
        numeric_cols = ["商品点击人数", "成交件数", "用户支付金额", "讲解次数"]
        # 定义需要保留第一个值的列
        keep_first_cols = ["直播间价格", "首次上架时间"]
        # 定义需要计算平均值的列
        avg_cols = ["商品点击-成交转化率（人数）"]

        agg_dict = {}

        # 添加求和列
        for col in numeric_cols:
            if col in self.df.columns:
                agg_dict[col] = "sum"

        # 添加保留第一个值的列
        for col in keep_first_cols:
            if col in self.df.columns:
                agg_dict[col] = "first"

        # 添加平均值列
        for col in avg_cols:
            if col in self.df.columns:
                agg_dict[col] = "mean"

        # 执行聚合
        self.aggregated_df = self.df.groupby("SKU").agg(agg_dict).reset_index()

        # 重新计算讲解效率
        if (
            "成交件数" in self.aggregated_df.columns
            and "讲解次数" in self.aggregated_df.columns
        ):
            self.aggregated_df["成交件数/每次讲解"] = (
                self.aggregated_df["成交件数"] / self.aggregated_df["讲解次数"]
            ).round(2)

        # 重新计算单次讲解成交金额（聚合后重新计算，而不是取平均值）
        if (
            "用户支付金额" in self.aggregated_df.columns
            and "讲解次数" in self.aggregated_df.columns
        ):
            # 避免除零错误
            mask = self.aggregated_df["讲解次数"] > 0
            self.aggregated_df.loc[mask, "单次讲解成交金额"] = (
                self.aggregated_df.loc[mask, "用户支付金额"] / self.aggregated_df.loc[mask, "讲解次数"]
            ).round(2)
            self.aggregated_df.loc[~mask, "单次讲解成交金额"] = 0

        logger.info(f"SKU聚合完成，共 {len(self.aggregated_df)} 个SKU")

    def get_session_comparison_data(self):
        """获取用于场次对比的数据，返回透视表格式"""
        if not self.session_data:
            return None

        # 合并所有场次数据
        all_data = []
        for session_name, df in self.session_data.items():
            df_copy = df.copy()
            df_copy["场次"] = session_name
            all_data.append(df_copy)

        combined_df = pd.concat(all_data, ignore_index=True)

        # 创建透视表
        comparison_data = {}
        numeric_cols = [
            "商品点击人数",
            "成交件数",
            "用户支付金额",
            "讲解次数",
            "成交件数/每次讲解",
            "单次讲解成交金额",
        ]

        for col in numeric_cols:
            if col in combined_df.columns:
                pivot_table = combined_df.pivot_table(
                    index="SKU", columns="场次", values=col, aggfunc="sum", fill_value=0
                )
                comparison_data[col] = pivot_table

        return comparison_data

    def get_session_names(self):
        """获取场次名称列表"""
        return list(self.session_data.keys())

    def get_session_data(self, session_name):
        """获取指定场次的数据"""
        return self.session_data.get(session_name)
