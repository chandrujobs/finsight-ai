import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from modules.data_extraction import extract_numeric_value

def create_financial_dashboard(extracted_data):
    """Create a dynamic financial dashboard from extracted data"""
    st.header("Financial Dashboard")
    
    # Organize data for visualization
    metrics = []
    values = []
    years = []
    companies = []
    
    for doc_name, doc_metrics in extracted_data.items():
        for metric_name, metric_data in doc_metrics.items():
            # Try to convert value to number for visualization
            value = extract_numeric_value(metric_data['value'])
            if value is not None:
                metrics.append(metric_name)
                values.append(value)
                years.append(metric_data.get('period', metric_data.get('year', 'Unknown')))
                companies.append(extracted_data[doc_name].get('company', doc_name))
    
    if not metrics:
        st.info("No numerical data available for dashboard visualization")
        return
    
    # Create a DataFrame for visualization
    df = pd.DataFrame({
        'Metric': metrics,
        'Value': values,
        'Year': years,
        'Company': companies
    })
    
    # Create visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Key Financial Metrics")
        
        # Plot as a horizontal bar chart
        fig = px.bar(
            df, 
            x='Value', 
            y='Metric', 
            color='Company', 
            barmode='group',
            title='Key Financial Metrics Comparison',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Metrics by Company/Year")
        
        # Create a scatter plot for metrics by year
        scatter_fig = px.scatter(
            df,
            x='Year',
            y='Value',
            size='Value',
            color='Company',
            hover_name='Metric',
            size_max=60,
            title='Financial Metrics Over Time'
        )
        st.plotly_chart(scatter_fig, use_container_width=True)
    
    # Show the raw data
    with st.expander("View Raw Data"):
        st.dataframe(df)

def plot_metric_comparison(comparison_df, metric_name):
    """Plot a comparison of a metric across different documents"""
    try:
        # Create bar chart
        fig = px.bar(
            comparison_df,
            x='Document',
            y='Numeric Value',
            color='Company',
            title=f'Comparison of {metric_name}',
            labels={'Numeric Value': metric_name, 'Document': 'Document'},
            text='Value'
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not create visualization: {str(e)}")

def plot_financial_projection(prediction_data):
    """Plot a financial projection with confidence intervals"""
    if not prediction_data:
        return
    
    all_years, all_values, predictions, r_squared = prediction_data
    
    # Create visualization data
    viz_data = {
        'Year': all_years,
        'Value': all_values,
        'Type': ['Historical' if year <= max(all_years) - len(predictions) else 'Projected' for year in all_years]
    }
    
    viz_df = pd.DataFrame(viz_data)
    
    # Create line chart
    fig = px.line(
        viz_df,
        x='Year',
        y='Value',
        color='Type',
        title=f'Historical and Projected Values (R² = {r_squared:.2f})',
        labels={'Value': 'Value', 'Year': 'Year'}
    )
    
    # Customize
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Value",
        legend_title="Data Type"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_metric_timeseries(df, metric_name):
    """Create a time series visualization of a specific metric"""
    # Filter for the specific metric
    filtered_df = df[df['Metric'] == metric_name]
    
    if filtered_df.empty:
        st.warning(f"No data available for {metric_name}")
        return
    
    # Sort by year
    filtered_df = filtered_df.sort_values('Year')
    
    # Create line chart
    fig = px.line(
        filtered_df,
        x='Year',
        y='Value',
        color='Company',
        markers=True,
        title=f'Time Series of {metric_name}',
        labels={'Value': metric_name, 'Year': 'Year'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_financial_summary_card(metric_name, value, previous_value=None, year=None):
    """Create a summary card for a financial metric"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(metric_name)
        st.write(f"**{value}**")
        if year:
            st.caption(f"Year: {year}")
    
    with col2:
        if previous_value:
            # Calculate change
            try:
                current = extract_numeric_value(value)
                previous = extract_numeric_value(previous_value)
                
                if current is not None and previous is not None and previous != 0:
                    percent_change = (current - previous) / previous * 100
                    arrow = "↑" if percent_change >= 0 else "↓"
                    color = "green" if percent_change >= 0 else "red"
                    
                    st.markdown(f'<span style="color:{color};font-size:24px">{arrow} {abs(percent_change):.1f}%</span>', unsafe_allow_html=True)
            except:
                pass