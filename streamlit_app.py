import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import DataLoader, logger

# 页面配置
st.set_page_config(
    page_title="数据分析可视化",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 缓存数据加载函数
@st.cache_data
def load_and_process_data():
    """加载和处理数据"""
    try:
        data_loader = DataLoader("data/20250701_y.xlsx")
        data_loader.get_sku_from_title()
        data_loader.clean_data()
        return data_loader.df
    except Exception as e:
        logger.error(f"数据加载失败: {e}")
        return None


def main():
    st.title("📊 数据分析可视化看板")
    st.markdown("---")

    # 加载数据
    df = load_and_process_data()

    if df is None:
        st.error("❌ 数据加载失败，请检查数据文件是否存在")
        return

    if df.empty:
        st.warning("⚠️ 数据为空")
        return

    # 侧边栏配置
    st.sidebar.header("🔧 数据配置")

    # 数据筛选
    st.sidebar.subheader("数据筛选")

    # SKU筛选（如果存在SKU列）
    if "SKU" in df.columns:
        unique_skus = df["SKU"].dropna().unique()
        if len(unique_skus) > 0:
            selected_skus = st.sidebar.multiselect(
                "选择SKU",
                options=unique_skus,
            )
            if selected_skus:
                df = df[df["SKU"].isin(selected_skus)]

    # 价格范围筛选
    if "直播间价格" in df.columns:
        price_min = float(df["直播间价格"].min())
        price_max = float(df["直播间价格"].max())
        price_range = st.sidebar.slider(
            "直播间价格范围",
            min_value=price_min,
            max_value=price_max,
            value=(price_min, price_max),
            format="¥%.2f",
        )
        df = df[
            (df["直播间价格"] >= price_range[0]) & (df["直播间价格"] <= price_range[1])
        ]

    # 排序选项
    st.sidebar.subheader("排序选项")
    numeric_columns = df.select_dtypes(include=["int64", "float64"]).columns.tolist()

    # 将成交件数/每次讲解设为默认排序选项（如果存在的话）
    default_sort = (
        "成交件数/每次讲解"
        if "成交件数/每次讲解" in numeric_columns
        else (
            "商品点击人数"
            if "商品点击人数" in numeric_columns
            else (numeric_columns[0] if numeric_columns else None)
        )
    )

    sort_column = st.sidebar.selectbox(
        "选择排序列",
        options=numeric_columns,
        index=(
            numeric_columns.index(default_sort)
            if default_sort and default_sort in numeric_columns
            else 0
        ),
    )
    sort_ascending = st.sidebar.radio("排序方向", options=["升序", "降序"]) == "升序"

    # 应用排序
    if sort_column:
        df = df.sort_values(by=sort_column, ascending=sort_ascending)

    # 主要内容区域
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 数据表格")
        st.dataframe(df, use_container_width=True, height=650)

    with col2:
        st.subheader("📈 数据概览")
        st.metric("总记录数", len(df))

        if "用户支付金额" in df.columns:
            total_payment = df["用户支付金额"].sum()
            avg_payment = df["用户支付金额"].mean()
            st.metric("总支付金额", f"¥{total_payment:,.2f}")
            st.metric("平均支付金额", f"¥{avg_payment:,.2f}")

        if "商品点击人数" in df.columns:
            total_clicks = df["商品点击人数"].sum()
            avg_clicks = df["商品点击人数"].mean()
            st.metric("总点击人数", f"{total_clicks:,}")
            st.metric("平均点击人数", f"{avg_clicks:.0f}")

        if "成交件数/每次讲解" in df.columns:
            avg_deal_per_explain = df["成交件数/每次讲解"].mean()
            max_deal_per_explain = df["成交件数/每次讲解"].max()
            st.metric("平均每次讲解成交件数", f"{avg_deal_per_explain:.2f}")
            st.metric("最高讲解效率", f"{max_deal_per_explain:.2f}")

    # 图表可视化区域
    st.markdown("---")
    st.subheader("📊 数据可视化")

    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(
        ["💰 价格分析", "👥 用户行为", "🎯 转化分析"]
    )

    with tab1:
        if "直播间价格" in df.columns and "用户支付金额" in df.columns:
            col1, col2 = st.columns(2)

            with col1:
                # 价格分布直方图
                fig_price_dist = px.histogram(
                    df, x="直播间价格", title="直播间价格分布", nbins=20
                )
                fig_price_dist.update_layout(xaxis_title="价格 (¥)", yaxis_title="频次")
                st.plotly_chart(fig_price_dist, use_container_width=True)

            with col2:
                # 价格对比散点图
                fig_price_compare = px.scatter(
                    df,
                    x="直播间价格",
                    y="用户支付金额",
                    title="直播间价格 vs 用户支付金额",
                    hover_data=["SKU"] if "SKU" in df.columns else None,
                )
                fig_price_compare.update_layout(
                    xaxis_title="直播间价格 (¥)", yaxis_title="用户支付金额 (¥)"
                )
                st.plotly_chart(fig_price_compare, use_container_width=True)

    with tab2:
        if "商品点击人数" in df.columns:
            col1, col2 = st.columns(2)

            with col1:
                # 点击人数排序选择
                st.write("**点击人数图表排序：**")
                clicks_sort_order = st.radio(
                    "排序方向",
                    options=["按点击数降序", "按点击数升序"],
                    key="clicks_sort",
                    horizontal=True,
                )

                # 按点击人数排序数据
                clicks_ascending = clicks_sort_order == "按点击数升序"
                df_sorted_clicks = df.sort_values(
                    by="商品点击人数", ascending=clicks_ascending
                )

                # 点击人数分布（按排序显示）
                fig_clicks = px.bar(
                    df_sorted_clicks,
                    x=(
                        "SKU"
                        if "SKU" in df_sorted_clicks.columns
                        else df_sorted_clicks.index
                    ),
                    y="商品点击人数",
                    title=f"商品点击人数 ({clicks_sort_order})",
                    hover_data=(["SKU"] if "SKU" in df_sorted_clicks.columns else None),
                )
                fig_clicks.update_layout(
                    xaxis_title="SKU", yaxis_title="点击人数", xaxis_tickangle=-45
                )
                st.plotly_chart(fig_clicks, use_container_width=True)

            with col2:
                if "成交件数/每次讲解" in df.columns:
                    # 讲解效率排序选择
                    st.write("**讲解效率图表排序：**")
                    efficiency_sort_order = st.radio(
                        "排序方向",
                        options=["按效率降序", "按效率升序"],
                        key="efficiency_sort",
                        horizontal=True,
                    )

                    # 按讲解效率排序数据
                    efficiency_ascending = efficiency_sort_order == "按效率升序"
                    df_sorted_efficiency = df.sort_values(
                        by="成交件数/每次讲解", ascending=efficiency_ascending
                    )

                    # 讲解效率条形图
                    fig_efficiency = px.bar(
                        df_sorted_efficiency,
                        x=(
                            "SKU"
                            if "SKU" in df_sorted_efficiency.columns
                            else df_sorted_efficiency.index
                        ),
                        y="成交件数/每次讲解",
                        title=f"每次讲解成交件数 ({efficiency_sort_order})",
                        hover_data=(["SKU"] if "SKU" in df_sorted_efficiency.columns else None),
                    )
                    fig_efficiency.update_layout(
                        xaxis_title="SKU", yaxis_title="成交件数/每次讲解", xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_efficiency, use_container_width=True)
                elif "讲解次数" in df.columns:
                    # 讲解次数 vs 点击人数
                    fig_explain_clicks = px.scatter(
                        df,
                        x="讲解次数",
                        y="商品点击人数",
                        title="讲解次数 vs 点击人数",
                        hover_data=["SKU"] if "SKU" in df.columns else None,
                    )
                    fig_explain_clicks.update_layout(
                        xaxis_title="讲解次数", yaxis_title="商品点击人数"
                    )
                    st.plotly_chart(fig_explain_clicks, use_container_width=True)

    with tab3:
        col1, col2 = st.columns(2)
        
        if "商品点击-成交转化率（人数）" in df.columns:
            with col1:
                # 转化率分布
                fig_conversion = px.histogram(
                    df, x="商品点击-成交转化率（人数）", title="转化率分布", nbins=20
                )
                fig_conversion.update_layout(
                    xaxis_title="转化率 (%)", yaxis_title="频次"
                )
                st.plotly_chart(fig_conversion, use_container_width=True)

            with col2:
                # 转化率 vs 用户支付金额
                if "用户支付金额" in df.columns:
                    fig_conversion_payment = px.scatter(
                        df,
                        x="商品点击-成交转化率（人数）",
                        y="用户支付金额",
                        title="转化率 vs 用户支付金额",
                        hover_data=["SKU"] if "SKU" in df.columns else None,
                    )
                    fig_conversion_payment.update_layout(
                        xaxis_title="转化率 (%)", yaxis_title="用户支付金额 (¥)"
                    )
                    st.plotly_chart(fig_conversion_payment, use_container_width=True)
        
        # 讲解效率分析
        if "成交件数/每次讲解" in df.columns:
            st.markdown("### 🎯 讲解效率分析")
            col3, col4 = st.columns(2)
            
            with col3:
                # 讲解效率分布
                fig_efficiency_dist = px.histogram(
                    df, x="成交件数/每次讲解", title="讲解效率分布", nbins=20
                )
                fig_efficiency_dist.update_layout(
                    xaxis_title="成交件数/每次讲解", yaxis_title="频次"
                )
                st.plotly_chart(fig_efficiency_dist, use_container_width=True)
            
            with col4:
                # 讲解效率 vs 转化率（如果转化率存在）
                if "商品点击-成交转化率（人数）" in df.columns:
                    fig_efficiency_conversion = px.scatter(
                        df,
                        x="成交件数/每次讲解",
                        y="商品点击-成交转化率（人数）",
                        title="讲解效率 vs 转化率",
                        hover_data=["SKU"] if "SKU" in df.columns else None,
                    )
                    fig_efficiency_conversion.update_layout(
                        xaxis_title="成交件数/每次讲解", yaxis_title="转化率 (%)"
                    )
                    st.plotly_chart(fig_efficiency_conversion, use_container_width=True)
                elif "用户支付金额" in df.columns:
                    # 讲解效率 vs 支付金额
                    fig_efficiency_payment = px.scatter(
                        df,
                        x="成交件数/每次讲解",
                        y="用户支付金额",
                        title="讲解效率 vs 用户支付金额",
                        hover_data=["SKU"] if "SKU" in df.columns else None,
                    )
                    fig_efficiency_payment.update_layout(
                        xaxis_title="成交件数/每次讲解", yaxis_title="用户支付金额 (¥)"
                    )
                    st.plotly_chart(fig_efficiency_payment, use_container_width=True)

    # 数据导出功能
    st.markdown("---")
    st.subheader("💾 数据导出")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("导出当前数据为CSV"):
            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="下载CSV文件",
                data=csv,
                file_name="filtered_data.csv",
                mime="text/csv",
            )

    with col2:
        if st.button("导出数据统计报告"):
            report = df.describe().to_csv(encoding="utf-8-sig")
            st.download_button(
                label="下载统计报告",
                data=report,
                file_name="data_report.csv",
                mime="text/csv",
            )

    with col3:
        st.info(f"当前显示 {len(df)} 条记录")


if __name__ == "__main__":
    main()
