import warnings
warnings.filterwarnings('ignore', category=UserWarning)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.data_processor import DataProcessor
from src.text_analyzer import SentimentAnalyzer, KeywordAnalyzer, TopicAnalyzer, InsightAnalyzer
from src.visualizer import Visualizer, SentimentVisualizer, KeywordVisualizer, TopicVisualizer, InsightVisualizer

def display_statistics(stats: dict):
    """显示统计指标"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总评论数", stats['total_reviews'])
    with col2:
        st.metric("平均评分", stats['average_rating'])
    with col3:
        st.metric("最近30天评论数", 
                 sum(count for date, count in stats['daily_reviews'].items() 
                     if datetime.strptime(str(date), '%Y-%m-%d').date() > 
                     datetime.now().date() - timedelta(days=30)))

def plot_rating_distribution(stats: dict):
    """绘制评分分布图"""
    df = pd.DataFrame(list(stats['rating_distribution'].items()),
                     columns=['评分', '数量'])
    fig = px.bar(df, x='评分', y='数量',
                 title='评分分布',
                 labels={'评分': '评分', '数量': '评论数量'})
    st.plotly_chart(fig)

def plot_daily_reviews(stats: dict):
    """绘制每日评论数量趋势图"""
    df = pd.DataFrame(list(stats['daily_reviews'].items()),
                     columns=['日期', '数量'])
    fig = px.line(df, x='日期', y='数量',
                  title='评论数量趋势',
                  labels={'日期': '日期', '数量': '评论数量'})
    st.plotly_chart(fig)

def show_keyword_analysis(df: pd.DataFrame, language: str):
    """
    显示关键词分析页面
    
    Args:
        df: 数据框
        language: 文本语言
    """
    st.header("关键词分析")
    
    # 初始化分析器
    keyword_analyzer = KeywordAnalyzer(language)
    keyword_visualizer = KeywordVisualizer()
    
    # 分析设置
    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider(
            "显示关键词数量",
            5, 50, 20,
            key="keyword_analysis_count_slider"
        )
    with col2:
        time_window = st.selectbox(
            "时间窗口",
            options=[("日", "D"), ("周", "W"), ("月", "M")],
            format_func=lambda x: x[0],
            index=1,
            key="keyword_analysis_time_window"
        )[1]
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["词云图", "关键词趋势", "评分关键词对比"])
    
    with tab1:
        st.subheader("词云分析")
        if st.button("生成词云", key="keyword_analysis_wordcloud_button"):
            with st.spinner("正在生成词云..."):
                # 提取关键词
                texts = df['content'].tolist()
                keywords = keyword_analyzer.extract_keywords(texts, top_n)
                
                # 生成词云图
                st.plotly_chart(
                    keyword_visualizer.create_wordcloud(keywords),
                    use_container_width=True
                )
    
    with tab2:
        st.subheader("关键词趋势分析")
        if st.button("分析趋势", key="keyword_analysis_trend_button"):
            with st.spinner("正在分析趋势..."):
                # 获取整体关键词
                all_keywords = keyword_analyzer.extract_keywords(
                    df['content'].tolist(),
                    top_n=10
                )
                
                # 计算趋势
                trend_df = keyword_analyzer.calculate_keyword_trends(
                    df,
                    list(all_keywords.keys()),
                    time_window
                )
                
                # 显示趋势图
                st.plotly_chart(
                    keyword_visualizer.create_keyword_trend_chart(trend_df),
                    use_container_width=True
                )
    
    with tab3:
        st.subheader("评分关键词对比")
        if st.button("分析评分关键词", key="keyword_analysis_rating_button"):
            with st.spinner("正在分析评分关键词..."):
                # 按评分提取关键词
                keywords_by_rating = keyword_analyzer.extract_keywords_by_rating(
                    df,
                    top_n=10
                )
                
                # 显示对比图
                st.plotly_chart(
                    keyword_visualizer.create_rating_keyword_comparison(keywords_by_rating),
                    use_container_width=True
                )
                
                # 显示详细结果
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### 高分评价常见关键词")
                    for word, weight in keywords_by_rating['positive'].items():
                        st.write(f"- {word}: {weight:.4f}")
                
                with col2:
                    st.markdown("##### 低分评价常见关键词")
                    for word, weight in keywords_by_rating['negative'].items():
                        st.write(f"- {word}: {weight:.4f}")

def show_topic_analysis(df: pd.DataFrame, language: str):
    """
    显示主题分析页面
    
    Args:
        df: 数据框
        language: 文本语言
    """
    st.header("主题聚类分析")
    
    # 初始化分析器
    topic_analyzer = TopicAnalyzer(language)
    topic_visualizer = TopicVisualizer()
    
    # 配置区
    col1, col2, col3 = st.columns(3)
    with col1:
        n_topics = st.slider("主题数量", 3, 10, 5)
    with col2:
        method = st.selectbox(
            "分析方法", 
            options=[("LDA主题模型", "lda"), ("KMeans聚类", "kmeans")],
            format_func=lambda x: x[0],
            index=0
        )[1]
    with col3:
        time_window = st.selectbox(
            "时间窗口",
            options=[("日", "D"), ("周", "W"), ("月", "M")],
            format_func=lambda x: x[0],
            index=1
        )[1]
    
    # 分析结果展示
    tab1, tab2, tab3, tab4 = st.tabs([
        "主题分布",
        "主题网络",
        "主题热力图",
        "主题趋势"
    ])
    
    if st.button("开始分析", key="start_topic_analysis"):
        with st.spinner("正在进行主题分析..."):
            # 获取文本数据
            texts = df['content'].tolist()
            
            # 执行主题分析
            topic_results = topic_analyzer.analyze_topics(
                texts,
                n_topics=n_topics,
                method=method
            )
            
            if topic_results:
                # 主题分布
                with tab1:
                    st.subheader("主题分布分析")
                    st.plotly_chart(
                        topic_visualizer.create_topic_distribution(topic_results),
                        use_container_width=True
                    )
                    
                    # 显示主题关键词
                    st.subheader("主题关键词")
                    for i, keywords in enumerate(topic_results['topics']):
                        with st.expander(f"主题 {i+1}"):
                            st.write("关键词：" + ", ".join(keywords))
                            if 'example_docs' in topic_results:
                                st.write("示例文档：")
                                for doc in topic_results['example_docs'].get(i, []):
                                    st.markdown(f"> {doc}")
                
                # 主题网络
                with tab2:
                    st.subheader("主题-关键词网络图")
                    st.plotly_chart(
                        topic_visualizer.create_topic_network(topic_results),
                        use_container_width=True
                    )
                
                # 主题热力图
                with tab3:
                    st.subheader("主题分布热力图")
                    if 'topic_distribution' in topic_results:
                        topic_dist_df = pd.DataFrame(
                            topic_results['topic_distribution'],
                            columns=[f"主题{i+1}" for i in range(n_topics)]
                        )
                        st.plotly_chart(
                            topic_visualizer.create_topic_heatmap(topic_dist_df),
                            use_container_width=True
                        )
                    else:
                        st.info("当前分析方法不支持主题分布热力图")
                
                # 主题趋势
                with tab4:
                    st.subheader("主题趋势分析")
                    trend_df = topic_analyzer.get_topic_trends(
                        df,
                        topic_results['document_topics'],
                        time_window
                    )
                    
                    if not trend_df.empty:
                        st.plotly_chart(
                            topic_visualizer.create_topic_trend(trend_df),
                            use_container_width=True
                        )
                    else:
                        st.warning("无法生成主题趋势图，可能是数据量不足")
                
                # 下载分析结果
                if st.download_button(
                    "下载分析结果",
                    data=pd.DataFrame({
                        'text': texts,
                        'topic': topic_results['document_topics']
                    }).to_csv(index=False),
                    file_name="topic_analysis_results.csv",
                    mime="text/csv"
                ):
                    st.success("分析结果已下载")

def show_insights_analysis(df: pd.DataFrame, language: str):
    """
    显示评论洞察分析页面
    
    Args:
        df: 数据框
        language: 文本语言
    """
    st.header("评论深度洞察")
    
    # 初始化分析器
    insight_analyzer = InsightAnalyzer(language)
    insight_visualizer = InsightVisualizer()
    
    if st.button("开始分析", key="start_insight_analysis"):
        with st.spinner("正在进行深度分析..."):
            # 提取洞察
            insights = insight_analyzer.extract_insights(df)
            
            if insights:
                # 显示异常检测结果
                st.subheader("异常评论检测")
                
                # 显示异常统计
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "异常评论数量",
                        insights['anomalies']['total']
                    )
                with col2:
                    st.metric(
                        "异常评论比例",
                        f"{insights['anomalies']['total']/len(df):.1%}"
                    )
                
                # 显示异常散点图
                st.plotly_chart(
                    insight_visualizer.create_anomaly_scatter(df),
                    use_container_width=True
                )
                
                # 显示相关性分析
                st.subheader("相关性分析")
                if insights.get('correlations'):
                    st.metric(
                        "评分-情感相关性",
                        f"{insights['correlations']['correlation']:.2f}"
                    )
                    st.metric(
                        "评分-情感一致性",
                        f"{insights['correlations']['consistency']:.1%}"
                    )

def main():
    # 设置页面配置
    st.set_page_config(
        page_title="顾客评论分析系统",
        page_icon="📊",
        layout="wide"
    )
    
    # 页面问题
    st.title("顾客评论分析系统")
    st.markdown("### 智能分析您的顾客评论数据")
    
    # 初始化处理器
    data_processor = DataProcessor()
    
    # 侧边
    with st.sidebar:
        st.header("配置选项")
        language = st.selectbox(
            "选择评论语言",
            ["中文", "英文", "双语"]
        )
        
        analysis_options = st.multiselect(
            "选择分析维度",
            options=["情感分析", "关键词分析", "主题聚类", "评分统计"],
            default=["情感分析", "关键词分析"]
        )
    
    # 主要内容区域
    tabs = st.tabs(["数据上传", "情感分析", "关键词分析", "主题分析", "洞察分析", "可视化展示"])
    
    with tabs[0]:
        st.header("数据上传")
        uploaded_file = st.file_uploader(
            "上传CSV或Excel文件",
            type=["csv", "xlsx"]
        )
        
        if uploaded_file is not None:
            try:
                # 读取CSV文件
                df = pd.read_csv(uploaded_file)
                
                # 验证必需的列是否存在
                required_columns = ['timestamp', 'content']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"CSV文件缺少必需的列: {', '.join(missing_columns)}")
                    st.info("请确保CSV文件包含以下列：timestamp（时间戳）和content（文本内容）")
                    return
                
                # 转换时间戳为datetime格式
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                except Exception as e:
                    st.error(f"时间戳格式转换失败：{str(e)}")
                    st.info("请确保timestamp列的格式为标准日期时间格式")
                    return
                
                # 初始化 filtered_df
                filtered_df = df.copy()
                
                # 显示数据预览
                st.subheader("数据预览")
                st.write(df.head())
                
                # 数据筛选部分
                st.subheader("数据筛选")
                # ... 筛选逻辑 ...
                
            except Exception as e:
                st.error(f"处理CSV文件时出现错误: {str(e)}")
                st.info("请确保CSV文件格式正确，并且包含所需的列")
    
    # 初始化分析器
    sentiment_analyzer = SentimentAnalyzer(language)
    sentiment_visualizer = SentimentVisualizer()
    
    with tabs[1]:
        st.header("情感分析")
        if 'df' not in locals():
            st.info("请先上传数据文件")
        else:
            try:
                # 初始化分析器
                sentiment_analyzer = SentimentAnalyzer(language)
                sentiment_visualizer = SentimentVisualizer()
                
                # 情感分析设置
                st.subheader("分析设置")
                batch_size = st.slider("批处理大小", 16, 64, 32)
                
                if st.button("开始分析"):
                    # 显示进度条
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    
                    try:
                        # 执行情感分析
                        texts = filtered_df['content'].tolist()
                        sentiment_results = SentimentAnalyzer.cached_analyze_batch(
                            texts=texts,
                            model_name=sentiment_analyzer.model_name,
                            device=str(sentiment_analyzer.device),
                            language=language,
                            batch_size=batch_size
                        )
                        
                        # 更新DataFrame
                        filtered_df['sentiment'] = [r['sentiment'] for r in sentiment_results]
                        filtered_df['confidence'] = [r['confidence'] for r in sentiment_results]
                        
                        # 计算统计信息
                        sentiment_stats = sentiment_analyzer.get_sentiment_stats(sentiment_results)
                        
                        # 显示结果
                        st.subheader("分析结果")
                        
                        # 显示基本统计信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "正面评论比例",
                                f"{sentiment_stats['sentiment_distribution'].get('正面', 0) / len(sentiment_results):.1%}"
                            )
                        with col2:
                            st.metric(
                                "负面评论比例",
                                f"{sentiment_stats['sentiment_distribution'].get('负面', 0) / len(sentiment_results):.1%}"
                            )
                        with col3:
                            st.metric(
                                "平均置信度",
                                f"{sentiment_stats['average_confidence']:.2f}"
                            )
                        
                        # 显示可视化结果
                        st.plotly_chart(
                            sentiment_visualizer.create_sentiment_distribution(sentiment_results)
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(
                                sentiment_visualizer.create_sentiment_trend(filtered_df)
                            )
                        with col2:
                            st.plotly_chart(
                                sentiment_visualizer.create_rating_sentiment_comparison(filtered_df)
                            )
                        
                        # 显示典型评论
                        st.subheader("典型评论示例")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("##### 典型正面评论")
                            for comment in sentiment_stats['typical_positive']:
                                st.markdown(f"""
                                > {comment['text']}  
                                > 置信度：{comment['confidence']:.2f}
                                """)
                        
                        with col2:
                            st.markdown("##### 典型负面评论")
                            for comment in sentiment_stats['typical_negative']:
                                st.markdown(f"""
                                > {comment['text']}  
                                > 置信度：{comment['confidence']:.2f}
                                """)
                        
                    except Exception as e:
                        st.error(f"情感分析过程出错：{str(e)}")
            except Exception as e:
                st.error(f"初始化情感分析器时出错：{str(e)}")
    
    with tabs[2]:
        if 'df' not in locals():
            st.info("请先上传数据文件")
        else:
            try:
                # 在这里调用 show_keyword_analysis，并添加随机后缀以确保 key 唯一
                import random
                import string
                random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                show_keyword_analysis_with_unique_keys(filtered_df, language, random_suffix)
            except Exception as e:
                st.error(f"关键词分析过程出错：{str(e)}")
    
    with tabs[3]:
        if 'df' not in locals():
            st.info("请先上传数据文件")
        else:
            try:
                show_topic_analysis(filtered_df, language)
            except Exception as e:
                st.error(f"主题分析过程出错：{str(e)}")
    
    with tabs[4]:
        if 'df' not in locals():
            st.info("请先上传数据文件")
        else:
            try:
                show_insights_analysis(filtered_df, language)
            except Exception as e:
                st.error(f"洞察分析过程出错：{str(e)}")
    
    with tabs[5]:
        st.header("可视化展示")
        if 'df' not in locals():
            st.info("请先上传数据文件")
        else:
            try:
                st.subheader("自定义图表")
                # 这里可以添加自��义可视化的代码
            except Exception as e:
                st.error(f"可视化过程出错：{str(e)}")

def show_keyword_analysis_with_unique_keys(df: pd.DataFrame, language: str, suffix: str):
    """
    显示关键词分析页面（带有唯一的key）
    
    Args:
        df: 数据框
        language: 文本语言
        suffix: 用于生成唯一key的后缀
    """
    st.header("关键词分析")
    
    # 初始化分析器
    keyword_analyzer = KeywordAnalyzer(language)
    keyword_visualizer = KeywordVisualizer()
    
    # 分析设置
    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider(
            "显示关键词数量",
            5, 50, 20,
            key=f"keyword_analysis_count_slider_{suffix}"
        )
    with col2:
        time_window = st.selectbox(
            "时间窗口",
            options=[("日", "D"), ("周", "W"), ("月", "M")],
            format_func=lambda x: x[0],
            index=1,
            key=f"keyword_analysis_time_window_{suffix}"
        )[1]
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["词云图", "关键词趋势", "评分关键词对比"])
    
    with tab1:
        st.subheader("词云分析")
        if st.button("生成词云", key=f"keyword_analysis_wordcloud_button_{suffix}"):
            with st.spinner("正在生成词云..."):
                texts = df['content'].tolist()
                keywords = keyword_analyzer.extract_keywords(texts, top_n)
                st.plotly_chart(
                    keyword_visualizer.create_wordcloud(keywords),
                    use_container_width=True
                )
    
    with tab2:
        st.subheader("关键词趋势分析")
        if st.button("分析趋势", key=f"keyword_analysis_trend_button_{suffix}"):
            with st.spinner("正在分析趋势..."):
                all_keywords = keyword_analyzer.extract_keywords(
                    df['content'].tolist(),
                    top_n=10
                )
                trend_df = keyword_analyzer.calculate_keyword_trends(
                    df,
                    list(all_keywords.keys()),
                    time_window
                )
                st.plotly_chart(
                    keyword_visualizer.create_keyword_trend_chart(trend_df),
                    use_container_width=True
                )
    
    with tab3:
        st.subheader("评分关键词对比")
        if st.button("分析评分关键词", key=f"keyword_analysis_rating_button_{suffix}"):
            with st.spinner("正在分析评分关键词..."):
                keywords_by_rating = keyword_analyzer.extract_keywords_by_rating(
                    df,
                    top_n=10
                )
                st.plotly_chart(
                    keyword_visualizer.create_rating_keyword_comparison(keywords_by_rating),
                    use_container_width=True
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### 高分评价常见关键词")
                    for word, weight in keywords_by_rating['positive'].items():
                        st.write(f"- {word}: {weight:.4f}")
                
                with col2:
                    st.markdown("##### 低分评价常见关键词")
                    for word, weight in keywords_by_rating['negative'].items():
                        st.write(f"- {word}: {weight:.4f}")

if __name__ == "__main__":
    main() 