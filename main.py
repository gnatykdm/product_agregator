import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import asyncio
from datetime import datetime

from services.basic_service import ParserClass
from services.amazon_service import AmazonService
from services.ebay_service import EbayService
from schema import ProductSchema
from logger import get_logger
from typing import List
from utill import replace_spaces

fig = go.Figure()

st.set_page_config(
    page_title="Product Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #EFECE3;
    }
    
    .stApp {
        background-color: #EFECE3;
    }
    
    [data-testid="stSidebar"] {
        background-color: #4A70A9;
    }
    
    [data-testid="stSidebar"] * {
        color: #EFECE3 !important;
    }
    
    [data-testid="stSidebar"] .stTextInput input {
        background-color: #EFECE3;
        color: #000000 !important;
        border: 1px solid #8FABD4;
        border-radius: 4px;
    }
    
    [data-testid="stSidebar"] button {
        background-color: #000000 !important;
        color: #EFECE3 !important;
        border: none;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: #8FABD4 !important;
        color: #000000 !important;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #000000;
        text-align: left;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .sub-header {
        font-size: 1rem;
        font-weight: 400;
        color: #4A70A9;
        text-align: left;
        margin-bottom: 2rem;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #000000;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: #4A70A9;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-container {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #4A70A9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #FFFFFF;
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #4A70A9;
        font-weight: 500;
        border-radius: 4px;
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4A70A9 !important;
        color: #EFECE3 !important;
    }
    
    .data-card {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    
    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #000000;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #8FABD4;
    }
    
    .stDataFrame {
        border: 1px solid #8FABD4;
        border-radius: 4px;
    }
    
    .product-card {
        background-color: #FFFFFF;
        padding: 1.25rem;
        border-radius: 8px;
        border-left: 4px solid #8FABD4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s;
    }
    
    .product-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-left-color: #4A70A9;
    }
    
    .stDownloadButton button {
        background-color: #4A70A9 !important;
        color: #EFECE3 !important;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 4px;
    }
    
    .stDownloadButton button:hover {
        background-color: #000000 !important;
    }
    
    .welcome-card {
        background: linear-gradient(135deg, #4A70A9 0%, #8FABD4 100%);
        padding: 3rem;
        border-radius: 12px;
        color: #EFECE3;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .feature-box {
        background-color: #FFFFFF;
        padding: 2rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 100%;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    div[data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #8FABD4;
        border-radius: 8px;
    }
    
    .stAlert {
        background-color: #FFFFFF;
        border-left: 4px solid #4A70A9;
        color: #000000;
    }
    </style>
""", unsafe_allow_html=True)

class MainParser:
    def __init__(self):
        self.ebay_parser: ParserClass = EbayService()
        self.amazon_parser: ParserClass = AmazonService()
        self.logger = get_logger("main-parser")
    
    async def merge_parse(self, prompt: str) -> List[ProductSchema]:
        self.logger.info(f"Starting concurrent parsing for: '{prompt}'")
        
        try:
            ebay_task = self.ebay_parser.parse(prompt)
            amazon_task = self.amazon_parser.parse(prompt)
            
            ebay_products, amazon_products = await asyncio.gather(
                ebay_task, 
                amazon_task,
                return_exceptions=True
            )
            
            if isinstance(ebay_products, Exception):
                self.logger.error(f"eBay parsing failed: {ebay_products}")
                ebay_products = []
            
            if isinstance(amazon_products, Exception):
                self.logger.error(f"Amazon parsing failed: {amazon_products}")
                amazon_products = []
            
            merged_products = ebay_products + amazon_products
            
            self.logger.info(
                f"Parsing complete - eBay: {len(ebay_products)}, "
                f"Amazon: {len(amazon_products)}, "
                f"Total: {len(merged_products)}"
            )
            
            return merged_products
        
        except Exception as e:
            self.logger.error(f"Error in merge_parse: {e}")
            return []
    
    def parse(self, prompt: str) -> List[ProductSchema]:
        return asyncio.run(self.merge_parse(prompt))

def insert_into_df(products: List[ProductSchema]) -> pd.DataFrame:
    if not products:
        return pd.DataFrame()
    
    data = []
    for product in products:
        data.append({
            'SOURCE': product.parsed_source.value,
            'TITLE': product.product_title,
            'PRICE': product.product_price,
            'RATING': product.product_rating,
            'VIEWS': product.product_views,
            'SOLD_OUT': product.product_sold_out,
            'URL': product.product_url,
            'IMAGE': product.product_image,
            'PARSED_DATE': product.product_parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    df = pd.DataFrame(data)
    return df

def create_price_comparison_chart(df: pd.DataFrame):
    fig = px.box(
        df, 
        x='SOURCE', 
        y='PRICE',
        color='SOURCE',
        title='Price Distribution Analysis',
        labels={'PRICE': 'Price (USD)', 'SOURCE': 'Marketplace'},
        color_discrete_map={'EBAY': '#4A70A9', 'AMAZON': '#8FABD4'}
    )
    fig.update_layout(
        showlegend=False, 
        height=400,
        plot_bgcolor='#EFECE3',
        paper_bgcolor='#FFFFFF',
        font=dict(color='#000000', family='Inter'),
        title_font=dict(size=16, color='#000000', family='Inter')
    )
    fig.update_xaxes(gridcolor='#8FABD4', gridwidth=0.5)
    fig.update_yaxes(gridcolor='#8FABD4', gridwidth=0.5)
    return fig

def create_price_scatter(df: pd.DataFrame):
    fig = px.scatter(
        df,
        x='PRICE',
        y='RATING',
        color='SOURCE',
        size='PRICE',
        hover_data=['TITLE'],
        title='Price vs Rating Correlation',
        labels={'PRICE': 'Price (USD)', 'RATING': 'Rating'},
        color_discrete_map={'EBAY': '#4A70A9', 'AMAZON': '#8FABD4'}
    )
    fig.update_layout(
        height=400,
        plot_bgcolor='#EFECE3',
        paper_bgcolor='#FFFFFF',
        font=dict(color='#000000', family='Inter'),
        title_font=dict(size=16, color='#000000', family='Inter')
    )
    fig.update_xaxes(gridcolor='#8FABD4', gridwidth=0.5)
    fig.update_yaxes(gridcolor='#8FABD4', gridwidth=0.5)
    return fig

def create_top_products_chart(df: pd.DataFrame, n: int = 10):
    top_df = df.nsmallest(n, 'PRICE')[['TITLE', 'PRICE', 'SOURCE']].copy()
    top_df['TITLE_SHORT'] = top_df['TITLE'].str[:45] + '...'
    
    fig = px.bar(
        top_df,
        x='PRICE',
        y='TITLE_SHORT',
        color='SOURCE',
        orientation='h',
        title=f'Top {n} Best Value Products',
        labels={'PRICE': 'Price (USD)', 'TITLE_SHORT': 'Product'},
        color_discrete_map={'EBAY': '#4A70A9', 'AMAZON': '#8FABD4'}
    )
    fig.update_layout(
        height=500, 
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='#EFECE3',
        paper_bgcolor='#FFFFFF',
        font=dict(color='#000000', family='Inter'),
        title_font=dict(size=16, color='#000000', family='Inter')
    )
    fig.update_xaxes(gridcolor='#8FABD4', gridwidth=0.5)
    return fig

def create_metrics_row(df: pd.DataFrame):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="TOTAL PRODUCTS",
            value=f"{len(df):,}",
            delta=None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        avg_price = df['PRICE'].mean()
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="AVERAGE PRICE",
            value=f"${avg_price:,.2f}",
            delta=None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        min_price = df['PRICE'].min()
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="MINIMUM PRICE",
            value=f"${min_price:,.2f}",
            delta=None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        max_price = df['PRICE'].max()
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="MAXIMUM PRICE",
            value=f"${max_price:,.2f}",
            delta=None
        )
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">Product Intelligence Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Platform Price Analysis & Market Intelligence System</p>', unsafe_allow_html=True)
    
    st.sidebar.title("SEARCH PARAMETERS")
    st.sidebar.markdown("---")
    
    search_query = st.sidebar.text_input(
        "Product Query",
        placeholder="Enter product name...",
        help="Input the product identifier for analysis"
    )
    
    search_button = st.sidebar.button("EXECUTE SEARCH", type="primary", use_container_width=True)
    
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'search_term' not in st.session_state:
        st.session_state.search_term = None
    
    if search_button and search_query:
        with st.spinner('Processing query... Fetching data from multiple sources...'):
            try:
                preprocessed = replace_spaces(search_query)
                service = MainParser()
                products = service.parse(preprocessed)
                
                if products:
                    df = insert_into_df(products)
                    st.session_state.df = df
                    st.session_state.search_term = search_query
                    st.success(f"✓ Query completed successfully. {len(products)} records retrieved.")
                else:
                    st.warning("⚠ No data returned. Please refine search parameters.")
            except Exception as e:
                st.error(f"✗ System Error: {str(e)}")
    
    if st.session_state.df is not None and not st.session_state.df.empty:
        df = st.session_state.df
        
        st.markdown(f'<div class="section-header">ANALYSIS RESULTS: {st.session_state.search_term.upper()}</div>', unsafe_allow_html=True)
        
        create_metrics_row(df)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["MARKET OVERVIEW", "PRICE ANALYTICS", "VALUE RANKING", "DATA EXPLORER"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="data-card">', unsafe_allow_html=True)
                source_counts = df['SOURCE'].value_counts()
                fig_pie = px.pie(
                    values=source_counts.values,
                    names=source_counts.index,
                    title='Marketplace Distribution',
                    color=source_counts.index,
                    color_discrete_map={'EBAY': '#4A70A9', 'AMAZON': '#8FABD4'}
                )
                fig_pie.update_layout(
                    height=400,
                    paper_bgcolor='#FFFFFF',
                    font=dict(color='#000000', family='Inter'),
                    title_font=dict(size=16, color='#000000', family='Inter')
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="data-card">', unsafe_allow_html=True)
                st.plotly_chart(create_price_comparison_chart(df), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="data-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">STATISTICAL SUMMARY BY MARKETPLACE</div>', unsafe_allow_html=True)
            stats_df = df.groupby('SOURCE')['PRICE'].agg(['mean', 'min', 'max', 'count']).round(2)
            stats_df.columns = ['Average Price ($)', 'Min Price ($)', 'Max Price ($)', 'Product Count']
            st.dataframe(stats_df, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.markdown('<div class="data-card">', unsafe_allow_html=True)
            if df['RATING'].notna().any():
                st.plotly_chart(create_price_scatter(df), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="data-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">PRICE SEGMENT DISTRIBUTION</div>', unsafe_allow_html=True)
                bins = [0, 100, 250, 500, 1000, float('inf')]
                labels = ['$0-100', '$100-250', '$250-500', '$500-1000', '$1000+']
                df['PRICE_RANGE'] = pd.cut(df['PRICE'], bins=bins, labels=labels)
                
                range_counts = df['PRICE_RANGE'].value_counts().sort_index()
                fig_bar = px.bar(
                    x=range_counts.index,
                    y=range_counts.values,
                    title='Products by Price Segment',
                    labels={'x': 'Price Range', 'y': 'Number of Products'},
                    color=range_counts.values,
                    color_continuous_scale=[[0, '#8FABD4'], [1, '#4A70A9']]
                )
                fig.update_layout(
                    plot_bgcolor='#EFECE3',
                    paper_bgcolor='#FFFFFF',
                    font=dict(color='#000000', family='Inter'),
                    title_font=dict(size=16, color='#000000', family='Inter')
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("⚠ Insufficient rating data for correlation analysis")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab3:
            st.markdown('<div class="data-card">', unsafe_allow_html=True)
            st.plotly_chart(create_top_products_chart(df, n=10), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="section-header">RECOMMENDED SELECTIONS</div>', unsafe_allow_html=True)
            recommended = df.nsmallest(5, 'PRICE')[['TITLE', 'PRICE', 'SOURCE', 'RATING', 'URL']].copy()
            
            for idx, row in recommended.iterrows():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{row['TITLE'][:80]}...**")
                with col2:
                    st.markdown(f"**${row['PRICE']:,.2f}**")
                with col3:
                    st.markdown(f"*{row['SOURCE']}*")
                
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    if pd.notna(row['RATING']):
                        st.markdown(f"Rating: {row['RATING']} ⭐")
                with col_b:
                    st.markdown(f"[View Details →]({row['URL']})")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab4:
            st.markdown('<div class="data-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">DATA REPOSITORY</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                source_filter = st.multiselect(
                    "Filter by Marketplace:",
                    options=df['SOURCE'].unique(),
                    default=df['SOURCE'].unique()
                )
            with col2:
                price_range = st.slider(
                    "Price Range Filter (USD):",
                    min_value=float(df['PRICE'].min()),
                    max_value=float(df['PRICE'].max()),
                    value=(float(df['PRICE'].min()), float(df['PRICE'].max()))
                )
            
            filtered_df = df[
                (df['SOURCE'].isin(source_filter)) &
                (df['PRICE'] >= price_range[0]) &
                (df['PRICE'] <= price_range[1])
            ]
            
            st.dataframe(
                filtered_df[['SOURCE', 'TITLE', 'PRICE', 'RATING', 'URL']],
                use_container_width=True,
                height=400
            )
            
            st.markdown(f"**Records Displayed:** {len(filtered_df):,} of {len(df):,}")
            
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="EXPORT TO CSV",
                data=csv,
                file_name=f"{replace_spaces(st.session_state.search_term)}_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.markdown("""
            <div class="welcome-card">
                <h2 style="margin-bottom: 1rem;">PRODUCT INTELLIGENCE PLATFORM</h2>
                <p style="font-size: 1.1rem;">Advanced Market Analysis & Price Intelligence System</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div class="feature-box">
                    <div class="feature-icon">📊</div>
                    <h3 style="color: #000000;">Advanced Analytics</h3>
                    <p style="color: #4A70A9;">Comprehensive data visualization and statistical analysis tools</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="feature-box">
                    <div class="feature-icon">🔍</div>
                    <h3 style="color: #000000;">Multi-Source Aggregation</h3>
                    <p style="color: #4A70A9;">Simultaneous data retrieval from major e-commerce platforms</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
                <div class="feature-box">
                    <div class="feature-icon">💾</div>
                    <h3 style="color: #000000;">Data Export</h3>
                    <p style="color: #4A70A9;">Export comprehensive reports for further analysis and documentation</p>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()