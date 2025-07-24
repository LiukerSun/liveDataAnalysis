import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
from utils import DataLoader, logger
from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.globals import ThemeType
import streamlit.components.v1 as components

# 页面配置
st.set_page_config(
    page_title="数据分析可视化",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 缓存数据加载函数
@st.cache_data
def load_and_process_data(data_source, source_type="folder"):
    """加载和处理数据"""
    try:
        if source_type == "folder":
            data_loader = DataLoader(data_source)
        elif source_type == "file_list":
            data_loader = DataLoader(data_source)
        else:
            data_loader = DataLoader(data_source)

        data_loader.get_sku_from_title()
        data_loader.clean_data()
        data_loader.aggregate_by_sku()
        return data_loader
    except Exception as e:
        logger.error(f"数据加载失败: {e}")
        return None


def create_trend_chart(comparison_data, metric, title):
    """创建SKU趋势折线图 - 使用pyecharts"""
    if metric not in comparison_data:
        return None

    pivot_data = comparison_data[metric]
    
    # 转置数据，便于绘制折线图
    trend_data = pivot_data.T
    
    # 精心挑选的高对比度颜色方案，便于区分多条线
    elegant_colors = [
        "#e60012", "#0070f3", "#00d084", "#ff6b00", "#8b5cf6", "#06b6d4",
        "#f59e0b", "#ef4444", "#10b981", "#3b82f6", "#8b5cf6", "#f97316",
        "#84cc16", "#06b6d4", "#f59e0b", "#ef4444", "#22c55e", "#6366f1",
        "#ec4899", "#14b8a6", "#f97316", "#84cc16", "#8b5cf6", "#06b6d4"
    ]
    
    # 获取所有场次名称（x轴）
    sessions = trend_data.index.tolist()
    
    # 创建折线图
    line_chart = Line(init_opts=opts.InitOpts(
        width="100%",
        height="600px",
        theme=ThemeType.LIGHT,
        bg_color="#ffffff"
    ))
    
    # 添加x轴
    line_chart.add_xaxis(xaxis_data=sessions)
    
    # 为每个SKU添加一条折线
    for i, sku in enumerate(trend_data.columns):
        color = elegant_colors[i % len(elegant_colors)]
        values = trend_data[sku].fillna(0).tolist()
        
        # 根据SKU数量调整线条样式
        line_width = 4 if len(trend_data.columns) <= 8 else 3 if len(trend_data.columns) <= 15 else 2
        symbol_size = 10 if len(trend_data.columns) <= 8 else 8 if len(trend_data.columns) <= 15 else 6
        
        line_chart.add_yaxis(
            series_name=str(sku),
            y_axis=values,
            color=color,
            symbol="circle",
            symbol_size=symbol_size,
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=line_width, opacity=0.9),
            itemstyle_opts=opts.ItemStyleOpts(
                color=color, 
                border_width=2, 
                border_color="#ffffff",
                opacity=0.9
            ),
            # 只对前5个SKU显示最值标记，避免图表过于复杂
            markpoint_opts=opts.MarkPointOpts(
                data=[
                    opts.MarkPointItem(type_="max", name="最大值"),
                    opts.MarkPointItem(type_="min", name="最小值")
                ]
            ) if i < 5 and len(values) > 1 else None,
            label_opts=opts.LabelOpts(is_show=False),
        )
    
    # 配置全局选项
    line_chart.set_global_opts(
        title_opts=opts.TitleOpts(
            title=title,
            title_textstyle_opts=opts.TextStyleOpts(
                font_size=18,
                font_weight="bold",
                color="#333333"
            ),
            pos_left="center",
            pos_top="20px"
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            axis_pointer_type="cross",
            background_color="rgba(245, 245, 245, 0.95)",
            border_width=1,
            border_color="#cccccc",
            textstyle_opts=opts.TextStyleOpts(color="#333333", font_size=12)
        ),
        legend_opts=opts.LegendOpts(
            type_="scroll",
            orient="horizontal" if len(trend_data.columns) <= 12 else "vertical",
            pos_left="center" if len(trend_data.columns) <= 12 else "right",
            pos_bottom="10px" if len(trend_data.columns) <= 12 else "middle",
            pos_right="10px" if len(trend_data.columns) > 12 else None,
            item_gap=12 if len(trend_data.columns) <= 12 else 8,
            textstyle_opts=opts.TextStyleOpts(font_size=11),
            selected_mode="multiple",
            page_button_item_gap=8,
            page_button_gap=10
        ),
        xaxis_opts=opts.AxisOpts(
            type_="category",
            name="场次",
            name_location="middle",
            name_gap=25,
            name_textstyle_opts=opts.TextStyleOpts(font_size=14, color="#666666"),
            axisline_opts=opts.AxisLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(color="#d0d0d0", width=1)
            ),
            axistick_opts=opts.AxisTickOpts(is_show=True),
            axislabel_opts=opts.LabelOpts(rotate=45 if len(sessions) > 8 else 0, font_size=11),
            splitline_opts=opts.SplitLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(color="#f0f0f0", width=1, type_="dashed")
            )
        ),
        yaxis_opts=opts.AxisOpts(
            type_="value",
            name=metric,
            name_location="middle",
            name_gap=40,
            name_textstyle_opts=opts.TextStyleOpts(font_size=14, color="#666666"),
            axisline_opts=opts.AxisLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(color="#d0d0d0", width=1)
            ),
            axistick_opts=opts.AxisTickOpts(is_show=True),
            axislabel_opts=opts.LabelOpts(font_size=11),
            splitline_opts=opts.SplitLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(color="#f0f0f0", width=1, type_="dashed")
            )
        ),
        datazoom_opts=[
            opts.DataZoomOpts(
                is_show=True,
                type_="slider",
                range_start=0,
                range_end=100,
                pos_bottom="60px"
            ),
            opts.DataZoomOpts(
                type_="inside",
                range_start=0,
                range_end=100
            )
        ] if len(sessions) > 10 else None,
        toolbox_opts=opts.ToolboxOpts(
            is_show=True,
            pos_right="20px",
            pos_top="60px"
        )
    )
    
    # 返回图表对象用于HTML渲染
    return line_chart


def display_session_comparison(data_loader):
    """显示场次对比分析"""
    st.subheader("📈 场次趋势对比")

    comparison_data = data_loader.get_session_comparison_data()
    if not comparison_data:
        st.warning("无法生成对比数据")
        return

    # 获取所有SKU列表
    all_skus = []
    for metric_data in comparison_data.values():
        all_skus.extend(metric_data.index.tolist())
    unique_skus = list(set(all_skus))

    # 添加SKU筛选控制
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 图表筛选控制")

    # SKU数量显示和筛选方式选择
    st.sidebar.info(f"总SKU数量: {len(unique_skus)}")
    
    # 智能默认筛选方式：如果SKU数量过多，默认使用"按表现排序"
    default_filter = "按表现排序" if len(unique_skus) > 15 else "限制数量"

    filter_method = st.sidebar.radio(
        "筛选方式",
        options=["按表现排序", "限制数量", "手动选择", "显示全部"],
        index=0,  # 默认选择第一个选项（按表现排序）
        help="选择如何筛选要在折线图中显示的SKU。建议使用'按表现排序'获得最佳视觉效果",
    )

    selected_skus = []  # 初始化为空，后续根据筛选方式确定

    if filter_method == "按表现排序":
        # 让用户选择排序指标
        metrics = list(comparison_data.keys())
        sort_metric = st.sidebar.selectbox(
            "排序指标", options=metrics, help="选择用于排序SKU的指标"
        )

        sort_direction = st.sidebar.radio(
            "排序方向", options=["降序", "升序"], horizontal=True
        )

        # 智能默认显示数量：根据总SKU数量动态调整
        default_top_n = min(12, max(5, len(unique_skus) // 3)) if len(unique_skus) > 15 else min(8, len(unique_skus))
        
        top_n = st.sidebar.slider(
            "显示前N个SKU",
            min_value=3,
            max_value=min(30, len(unique_skus)),
            value=default_top_n,
            help="显示排序后前N个表现最好/最差的SKU。建议不超过15个以保持图表清晰",
        )

        # 按照选定指标排序SKU
        if sort_metric in comparison_data:
            metric_data = comparison_data[sort_metric]
            # 计算每个SKU的总和或平均值进行排序
            sku_performance = metric_data.sum(axis=1).sort_values(
                ascending=(sort_direction == "升序")
            )
            selected_skus = sku_performance.head(top_n).index.tolist()
        else:
            selected_skus = unique_skus[:top_n]
            
    elif filter_method == "限制数量":
        # 智能默认数量
        default_max = min(10, max(5, len(unique_skus) // 4)) if len(unique_skus) > 20 else min(8, len(unique_skus))
        
        max_display = st.sidebar.slider(
            "最大显示SKU数量",
            min_value=3,
            max_value=min(25, len(unique_skus)),
            value=default_max,
            help="限制在图表中显示的SKU数量。建议不超过15个以保持图表清晰",
        )
        selected_skus = unique_skus[:max_display]
        
    elif filter_method == "手动选择":
        # 智能默认选择：选择前几个，但不要太多
        default_selection = unique_skus[:min(8, len(unique_skus))]
        
        selected_skus = st.sidebar.multiselect(
            "选择要显示的SKU",
            options=unique_skus,
            default=default_selection,
            help="手动选择要在图表中显示的SKU。建议选择不超过15个以保持图表清晰",
        )
    elif filter_method == "显示全部":
        selected_skus = unique_skus
        if len(unique_skus) > 20:
            st.sidebar.warning(f"⚠️ 当前将显示全部{len(unique_skus)}个SKU，图表可能较为拥挤。建议使用其他筛选方式以获得更好的视觉效果。")

    # 如果没有选择任何SKU，显示警告
    if not selected_skus:
        st.warning("⚠️ 请至少选择一个SKU进行显示")
        return

    # 显示信息和提示
    col_info1, col_info2 = st.columns([2, 1])
    with col_info1:
        st.info(f"📊 当前显示 {len(selected_skus)} 个SKU的趋势图表")
    with col_info2:
        if len(selected_skus) > 15:
            st.warning("⚠️ SKU数量较多，建议减少显示数量以获得更好的视觉效果")
        elif len(selected_skus) > 8:
            st.info("💡 提示：可以点击图例来隐藏/显示特定的SKU线条")
        else:
            st.success("✅ 当前显示数量适中，图表清晰易读")

    # 创建选项卡
    metrics = list(comparison_data.keys())
    tabs = st.tabs([f"📊 {metric}" for metric in metrics])

    for i, metric in enumerate(metrics):
        with tabs[i]:
            col1, col2 = st.columns([3, 1])

            with col1:
                # 趋势折线图（筛选后的SKU）
                filtered_comparison_data = {}
                filtered_comparison_data[metric] = comparison_data[metric].loc[
                    comparison_data[metric].index.intersection(selected_skus)
                ]

                chart = create_trend_chart(
                    filtered_comparison_data,
                    metric,
                    f"各SKU {metric} 趋势 (显示{len(selected_skus)}个SKU)",
                )
                if chart:
                    # 渲染图表为HTML
                    chart_html = chart.render_embed()
                    components.html(chart_html, height=650)

            with col2:
                # 数据表格（显示所有数据，但高亮显示选中的）
                st.write(f"**{metric} 数据表**")
                pivot_data = comparison_data[metric]

                # 如果筛选了SKU，高亮显示选中的行
                if len(selected_skus) < len(unique_skus):
                    # 创建样式化的DataFrame
                    styled_df = pivot_data.style.apply(
                        lambda x: [
                            (
                                "background-color: #e6f3ff"
                                if x.name in selected_skus
                                else ""
                            )
                            for _ in x
                        ],
                        axis=1,
                    )
                    st.dataframe(styled_df, use_container_width=True)
                else:
                    st.dataframe(pivot_data, use_container_width=True)


def display_single_session_analysis(data_loader, selected_session):
    """显示单场数据分析"""
    session_data = data_loader.get_session_data(selected_session)
    if session_data is None or session_data.empty:
        st.error(f"场次 {selected_session} 数据为空")
        return

    st.subheader(f"📋 {selected_session} 数据分析")

    # 数据概览
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("SKU数量", len(session_data))

    with col2:
        if "用户支付金额" in session_data.columns:
            total_payment = session_data["用户支付金额"].sum()
            st.metric("总支付金额", f"¥{total_payment:,.2f}")

    with col3:
        if "商品点击人数" in session_data.columns:
            total_clicks = session_data["商品点击人数"].sum()
            st.metric("总点击人数", f"{total_clicks:,}")

    with col4:
        if "成交件数" in session_data.columns:
            total_deals = session_data["成交件数"].sum()
            st.metric("总成交件数", f"{total_deals:,}")

    # 数据表格
    st.dataframe(session_data, use_container_width=True, height=400)


def main():
    st.title("📊 多场直播数据分析可视化看板")
    st.markdown("---")

    # 数据源配置
    st.sidebar.header("📁 数据源配置")

    # 数据源选择
    data_source_type = st.sidebar.radio(
        "选择数据源类型",
        options=["文件夹", "单个文件"],
        help="选择文件夹可自动加载所有xlsx文件，选择单个文件适用于单场分析",
    )

    data_source = None
    if data_source_type == "文件夹":
        # 使用文件输入选择文件夹中的文件
        data_folder = st.sidebar.text_input(
            "数据文件夹路径", value="data", help="输入包含excel文件的文件夹路径"
        )
        if os.path.exists(data_folder) and os.path.isdir(data_folder):
            data_source = data_folder
        else:
            st.sidebar.error("文件夹路径不存在")
    else:
        # 单个文件选择
        data_file = st.sidebar.text_input(
            "数据文件路径", value="data/20250701_1.xlsx", help="输入excel文件路径"
        )
        if os.path.exists(data_file) and os.path.isfile(data_file):
            data_source = data_file
        else:
            st.sidebar.error("文件路径不存在")

    if not data_source:
        st.warning("⚠️ 请配置正确的数据源路径")
        return

    # 加载数据
    data_loader = load_and_process_data(
        data_source, data_source_type.lower().replace(" ", "_")
    )

    if data_loader is None:
        st.error("❌ 数据加载失败，请检查数据文件是否存在")
        return

    # 获取场次信息
    session_names = data_loader.get_session_names()
    if not session_names:
        st.error("❌ 没有找到有效的场次数据")
        return

    st.sidebar.markdown("---")
    st.sidebar.header("🔧 分析配置")

    # 分析视图选择
    analysis_view = st.sidebar.selectbox(
        "选择分析视图",
        options=["聚合分析", "场次对比", "单场分析"],
        help="聚合分析：按SKU汇总所有场次数据；场次对比：查看SKU在不同场次的趋势；单场分析：分析单个场次数据",
    )

    # 根据分析视图显示相应配置
    if analysis_view == "单场分析":
        selected_session = st.sidebar.selectbox("选择场次", options=session_names)

    # 主要内容区域
    if analysis_view == "聚合分析":
        # 显示聚合数据分析
        df = data_loader.aggregated_df
        if df is None or df.empty:
            st.error("❌ 聚合数据为空")
            return

        st.subheader("📊 SKU聚合数据分析")
        st.info(f"已聚合 {len(session_names)} 场数据，共 {len(df)} 个SKU")

        # 侧边栏筛选配置
        st.sidebar.subheader("数据筛选")

        # SKU筛选
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
            if price_min != price_max:
                price_range = st.sidebar.slider(
                    "直播间价格范围",
                    min_value=price_min,
                    max_value=price_max,
                    value=(price_min, price_max),
                    format="¥%.2f",
                )
                df = df[
                    (df["直播间价格"] >= price_range[0])
                    & (df["直播间价格"] <= price_range[1])
                ]

        # 排序选项
        st.sidebar.subheader("排序选项")
        numeric_columns = df.select_dtypes(
            include=["int64", "float64"]
        ).columns.tolist()

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
        sort_ascending = (
            st.sidebar.radio("排序方向", options=["升序", "降序"]) == "升序"
        )

        # 应用排序
        if sort_column:
            df = df.sort_values(by=sort_column, ascending=sort_ascending)

        # 显示数据概览和表格
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📋 聚合数据表格")
            st.dataframe(df, use_container_width=True, height=650)

        with col2:
            st.subheader("📈 数据概览")
            st.metric("SKU数量", len(df))
            st.metric("场次数量", len(session_names))

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
                st.metric("平均讲解效率", f"{avg_deal_per_explain:.2f}")
                st.metric("最高讲解效率", f"{max_deal_per_explain:.2f}")

        # 图表可视化区域（保持原有的可视化逻辑）
        st.markdown("---")
        st.subheader("📊 数据可视化")

        # 创建选项卡
        tab1, tab2, tab3 = st.tabs(["💰 价格分析", "👥 用户行为", "🎯 转化分析"])

        with tab1:
            if "直播间价格" in df.columns and "用户支付金额" in df.columns:
                col1, col2 = st.columns(2)

                with col1:
                    # 价格分布直方图
                    fig_price_dist = px.histogram(
                        df, x="直播间价格", title="直播间价格分布", nbins=20
                    )
                    fig_price_dist.update_layout(
                        xaxis_title="价格 (¥)", yaxis_title="频次"
                    )
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
                        x="SKU",
                        y="商品点击人数",
                        title=f"商品点击人数 ({clicks_sort_order})",
                        hover_data=["SKU"],
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
                            x="SKU",
                            y="成交件数/每次讲解",
                            title=f"每次讲解成交件数 ({efficiency_sort_order})",
                            hover_data=["SKU"],
                        )
                        fig_efficiency.update_layout(
                            xaxis_title="SKU",
                            yaxis_title="成交件数/每次讲解",
                            xaxis_tickangle=-45,
                        )
                        st.plotly_chart(fig_efficiency, use_container_width=True)

        with tab3:
            col1, col2 = st.columns(2)

            if "商品点击-成交转化率（人数）" in df.columns:
                with col1:
                    # 转化率分布
                    fig_conversion = px.histogram(
                        df,
                        x="商品点击-成交转化率（人数）",
                        title="转化率分布",
                        nbins=20,
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
                        st.plotly_chart(
                            fig_conversion_payment, use_container_width=True
                        )

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
                        st.plotly_chart(
                            fig_efficiency_conversion, use_container_width=True
                        )
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
                            xaxis_title="成交件数/每次讲解",
                            yaxis_title="用户支付金额 (¥)",
                        )
                        st.plotly_chart(
                            fig_efficiency_payment, use_container_width=True
                        )

    elif analysis_view == "场次对比":
        # 显示场次对比分析
        display_session_comparison(data_loader)

    elif analysis_view == "单场分析":
        # 显示单场数据分析
        display_single_session_analysis(data_loader, selected_session)

    # 数据导出功能
    st.markdown("---")
    st.subheader("💾 数据导出")

    col1, col2, col3 = st.columns(3)

    # 根据当前视图确定要导出的数据
    export_df = None
    if analysis_view == "聚合分析":
        export_df = data_loader.aggregated_df
    elif analysis_view == "单场分析":
        export_df = data_loader.get_session_data(selected_session)
    else:
        export_df = data_loader.df

    if export_df is not None and not export_df.empty:
        with col1:
            if st.button("导出当前数据为CSV"):
                csv = export_df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="下载CSV文件",
                    data=csv,
                    file_name=f"{analysis_view}_data.csv",
                    mime="text/csv",
                )

        with col2:
            if st.button("导出数据统计报告"):
                report = export_df.describe().to_csv(encoding="utf-8-sig")
                st.download_button(
                    label="下载统计报告",
                    data=report,
                    file_name=f"{analysis_view}_report.csv",
                    mime="text/csv",
                )

        with col3:
            st.info(f"当前显示 {len(export_df)} 条记录")


if __name__ == "__main__":
    main()
