import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from wordcloud import WordCloud
import numpy as np
from data_processor import extract_common_words, analyze_response_times

def plot_importance_distribution(df):
    """Plot distribution of email importance."""
    if df.empty or 'importance' not in df.columns:
        return go.Figure()
    
    importance_counts = df['importance'].value_counts()
    
    fig = go.Figure(data=[
        go.Bar(
            x=importance_counts.index,
            y=importance_counts.values,
            marker_color=['red' if x == 'high' else 'blue' for x in importance_counts.index]
        )
    ])
    
    fig.update_layout(
        title='Email Importance Distribution',
        xaxis_title='Importance Level',
        yaxis_title='Count'
    )
    
    return fig

def plot_email_volume_over_time(df):
    """Plot email volume over time."""
    if df.empty or 'date' not in df.columns:
        # Return empty figure if no data
        return go.Figure()
    
    # Resample data by day
    df['date_only'] = df['date'].dt.date
    daily_counts = df.groupby(['date_only', 'is_sent']).size().unstack(fill_value=0).reset_index()
    
    # Rename columns
    if True in daily_counts.columns:
        daily_counts.rename(columns={True: 'Sent'}, inplace=True)
    else:
        daily_counts['Sent'] = 0
        
    if False in daily_counts.columns:
        daily_counts.rename(columns={False: 'Received'}, inplace=True)
    else:
        daily_counts['Received'] = 0
    
    # Create a line chart with both sent and received
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_counts['date_only'],
        y=daily_counts['Received'],
        mode='lines',
        name='Received',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_counts['date_only'],
        y=daily_counts['Sent'],
        mode='lines',
        name='Sent',
        line=dict(color='green', width=2)
    ))
    
    # Calculate total (sent + received)
    daily_counts['Total'] = daily_counts['Sent'] + daily_counts['Received']
    
    fig.add_trace(go.Scatter(
        x=daily_counts['date_only'],
        y=daily_counts['Total'],
        mode='lines',
        name='Total',
        line=dict(color='red', width=2)
    ))
    
    # Update layout
    fig.update_layout(
        title='Email Volume Over Time',
        xaxis_title='Date',
        yaxis_title='Number of Emails',
        legend_title='Email Type',
        hovermode='x unified'
    )
    
    return fig

def plot_email_categories(df):
    """Plot email category distribution."""
    if df.empty or 'category' not in df.columns:
        return go.Figure()
    
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['Category', 'Count']
    
    fig = px.pie(
        category_counts, 
        values='Count', 
        names='Category',
        title='Email Categories',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        uniformtext_minsize=12, 
        uniformtext_mode='hide'
    )
    
    return fig

def plot_sender_distribution(df):
    """Plot top email senders distribution."""
    if df.empty or 'from' not in df.columns:
        return go.Figure()
    
    # Get top 10 senders
    sender_counts = df['from'].value_counts().head(10).reset_index()
    sender_counts.columns = ['Sender', 'Count']
    
    # Truncate long email addresses
    sender_counts['Sender'] = sender_counts['Sender'].apply(
        lambda x: x[:20] + '...' if len(x) > 20 else x
    )
    
    fig = px.bar(
        sender_counts,
        x='Count',
        y='Sender',
        orientation='h',
        title='Top Email Senders',
        color='Count',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title='Number of Emails',
        yaxis_title='Sender',
        showlegend=False
    )
    
    return fig

def plot_hourly_distribution(df):
    """Plot email activity by hour of day."""
    if df.empty or 'date' not in df.columns:
        return go.Figure()
    
    # Extract hour from datetime
    df['hour'] = df['date'].dt.hour
    
    # Count emails by hour and sent/received status
    hourly_counts = df.groupby(['hour', 'is_sent']).size().unstack(fill_value=0).reset_index()
    
    # Rename columns
    if True in hourly_counts.columns:
        hourly_counts.rename(columns={True: 'Sent'}, inplace=True)
    else:
        hourly_counts['Sent'] = 0
        
    if False in hourly_counts.columns:
        hourly_counts.rename(columns={False: 'Received'}, inplace=True)
    else:
        hourly_counts['Received'] = 0
    
    fig = go.Figure()
    
    # Add bar for received emails
    fig.add_trace(go.Bar(
        x=hourly_counts['hour'],
        y=hourly_counts['Received'],
        name='Received',
        marker_color='blue'
    ))
    
    # Add bar for sent emails
    fig.add_trace(go.Bar(
        x=hourly_counts['hour'],
        y=hourly_counts['Sent'],
        name='Sent',
        marker_color='green'
    ))
    
    # Update layout
    fig.update_layout(
        title='Email Activity by Hour of Day',
        xaxis_title='Hour (24-hour format)',
        yaxis_title='Number of Emails',
        barmode='group',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(24)),
            ticktext=[f"{h}:00" for h in range(24)]
        )
    )
    
    return fig

def plot_word_cloud(df, column='subject'):
    """Generate a word cloud from email subjects."""
    if df.empty or column not in df.columns:
        # Return empty figure if no data
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Extract common words
    word_counts = extract_common_words(df, column)
    
    if not word_counts:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No significant words found', ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Create word cloud
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white',
        max_words=100,
        colormap='viridis',
        contour_width=1
    ).generate_from_frequencies(dict(word_counts))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    return fig

def plot_response_times(df):
    """Plot email response time analysis."""
    response_df = analyze_response_times(df)
    
    if response_df.empty:
        return go.Figure()
    
    # Separate my responses from others' responses
    my_responses = response_df[response_df['is_sent_by_me']]
    others_responses = response_df[~response_df['is_sent_by_me']]
    
    # Calculate statistics
    my_avg_response = my_responses['response_time_hours'].mean() if not my_responses.empty else 0
    others_avg_response = others_responses['response_time_hours'].mean() if not others_responses.empty else 0
    
    # Create histogram of response times
    fig = go.Figure()
    
    # Add histogram for my response times
    if not my_responses.empty:
        fig.add_trace(go.Histogram(
            x=my_responses['response_time_hours'],
            name='My Response Times',
            opacity=0.7,
            marker_color='green',
            nbinsx=20,
            histnorm='probability'
        ))
    
    # Add histogram for others' response times
    if not others_responses.empty:
        fig.add_trace(go.Histogram(
            x=others_responses['response_time_hours'],
            name="Others' Response Times",
            opacity=0.7,
            marker_color='blue',
            nbinsx=20,
            histnorm='probability'
        ))
    
    # Add vertical lines for average response times
    if not my_responses.empty:
        fig.add_vline(
            x=my_avg_response, 
            line_width=2, 
            line_dash="dash", 
            line_color="green",
            annotation_text=f"My Avg: {my_avg_response:.1f}h",
            annotation_position="top right"
        )
    
    if not others_responses.empty:
        fig.add_vline(
            x=others_avg_response, 
            line_width=2, 
            line_dash="dash", 
            line_color="blue",
            annotation_text=f"Others Avg: {others_avg_response:.1f}h",
            annotation_position="top right"
        )
    
    # Update layout
    fig.update_layout(
        title='Email Response Time Distribution',
        xaxis_title='Response Time (hours)',
        yaxis_title='Frequency (normalized)',
        barmode='overlay',
        xaxis=dict(range=[0, min(48, response_df['response_time_hours'].max() + 1)])
    )
    
    return fig
