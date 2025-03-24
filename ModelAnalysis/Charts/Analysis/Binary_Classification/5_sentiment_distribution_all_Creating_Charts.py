import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Create output directory if it doesn't exist
os.makedirs('comment_visualizations', exist_ok=True)

# Load the CSV file

df = pd.read_csv('../ModelAnalysis/Charts/Analysis/Binary_Classification/with_context/binary-classification-with-context.csv', sep=';')
df = pd.read_csv('../ModelAnalysis/Charts/Analysis/Binary_Classification/without_context/binary-classification-zero-context.csv', sep=';')

# Function to visualize sentiment for a single comment
def visualize_single_comment(comment_idx):
    row = df.iloc[comment_idx]
    comment = row['Comment']
    sentiments = row.iloc[1:].values
    models = df.columns[1:]
    
    # Define color mapping for sentiments
    sentiment_colors = {
        'POSITIVE': '#4CAF50',  # Green
        'NEGATIVE': '#F44336'   # Red
    }
    
    # Create a numeric representation for plotting
    sentiment_numeric = []
    colors = []
    clean_sentiments = []
    
    for sentiment in sentiments:
        if pd.isna(sentiment):
            sentiment_numeric.append(0)
            colors.append('#CCCCCC')  # Gray for NaN
            clean_sentiments.append('N/A')
        else:
            clean_sentiments.append(sentiment)
            colors.append(sentiment_colors[sentiment])
            if sentiment == 'POSITIVE':
                sentiment_numeric.append(1)
            else:  # NEGATIVE
                sentiment_numeric.append(-1)
    
    # Sort models by sentiment (optional)
    sorted_data = sorted(zip(models, sentiment_numeric, colors, clean_sentiments), 
                        key=lambda x: (x[1], x[0]))
    models, sentiment_numeric, colors, clean_sentiments = zip(*sorted_data)
    
    # Create figure with adequate size for readability
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot horizontal bars
    bars = ax.barh(range(len(models)), sentiment_numeric, color=colors)
    
    # Add sentiment labels directly on the bars
    for i, bar in enumerate(bars):
        sentiment_text = clean_sentiments[i]
        x_pos = bar.get_width() + 0.05
        ax.text(x_pos, i, sentiment_text, va='center', fontweight='bold')
    
    # Set y-tick labels
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([model for model in models])
    
    # Set x-axis
    ax.set_xlim([-1.5, 1.5])
    ax.set_xticks([-1, 1])
    ax.set_xticklabels(['NEGATIVE', 'POSITIVE'])
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    
    # Highlight human annotation
    human_idx = list(models).index('Human Annotator')
    ax.get_yticklabels()[human_idx].set_fontweight('bold')
    ax.get_yticklabels()[human_idx].set_color('blue')
    
    # Add grid for better readability
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Set title and labels
    ax.set_title(f'Comment: "{comment}" - Sentiment Analysis', fontsize=14)
    ax.set_xlabel('Sentiment Classification', fontsize=12)
    ax.set_ylabel('Model', fontsize=12)
    
    # Add a legend for sentiment colors
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4CAF50', label='POSITIVE'),
        Patch(facecolor='#F44336', label='NEGATIVE')
    ]
    ax.legend(handles=legend_elements, title='Sentiment', loc='lower right')
    
    # Tight layout
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(f'comment_visualizations/{comment}_sentiment.png', dpi=300, bbox_inches='tight')
    
    return fig

# Create individual visualizations for each comment
for i in range(len(df)):
    print(f"Creating visualization for {df.iloc[i]['Comment']}...")
    fig = visualize_single_comment(i)
    plt.close(fig)  # Close the figure to free memory

# Create aggregate analysis visualizations

# 1. Model Agreement with Human Annotations
def create_agreement_visualization():
    # Calculate agreement rates
    human_sentiment = df['Human Annotator']
    agreement_rates = {}
    
    for model in df.columns[2:]:  # Skip 'Comment' and 'MODUS Human Annotator Sentiment'
        agreement = sum(df[model] == human_sentiment) / len(df) * 100
        agreement_rates[model] = agreement
    
    # Sort by agreement rate
    agreement_df = pd.DataFrame(list(agreement_rates.items()), columns=['Model', 'Agreement Rate'])
    agreement_df = agreement_df.sort_values('Agreement Rate', ascending=False)
    
    # Create color gradient based on agreement rate
    colors = ['#5e4fa2', '#3288bd', '#66c2a5', '#abdda4', '#e6f598', 
              '#fee08b', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
    normalized_rates = (agreement_df['Agreement Rate'] - agreement_df['Agreement Rate'].min()) / \
                       (agreement_df['Agreement Rate'].max() - agreement_df['Agreement Rate'].min())
    color_indices = (normalized_rates * (len(colors) - 1)).astype(int)
    bar_colors = [colors[i] for i in color_indices]
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.barh(agreement_df['Model'], agreement_df['Agreement Rate'], color=bar_colors)
    
    # Add percentage labels
    for i, v in enumerate(agreement_df['Agreement Rate']):
        ax.text(v + 1, i, f"{v:.1f}%", va='center')
    
    ax.set_xlim(0, 100)
    ax.set_title('Model Agreement with Human Annotations (%)', fontsize=14)
    ax.set_xlabel('Agreement Rate (%)', fontsize=12)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('overall_model_agreement.png', dpi=300, bbox_inches='tight')
    plt.close()

# 2. Sentiment Distribution by Model
def create_distribution_visualization():
    # Calculate sentiment distribution for each model
    models = df.columns[1:]  # Skip 'Comment'
    sentiments = ['POSITIVE', 'NEGATIVE']
    
    # Prepare data for plotting
    data_for_plot = []
    
    for model in models:
        sentiment_counts = {
            'POSITIVE': sum(df[model] == 'POSITIVE') / len(df) * 100,
            'NEGATIVE': sum(df[model] == 'NEGATIVE') / len(df) * 100
        }
        
        data_for_plot.append({
            'Model': model,
            'POSITIVE': sentiment_counts['POSITIVE'],
            'NEGATIVE': sentiment_counts['NEGATIVE']
        })
    
    # Convert to DataFrame
    dist_df = pd.DataFrame(data_for_plot)
    
    # Sort by percentage of positive sentiment (optional)
    dist_df = dist_df.sort_values('POSITIVE', ascending=False)
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 10))
    
    bottom_values = np.zeros(len(dist_df))
    
    # Plot stacked bars
    for sentiment in sentiments:
        color = '#4CAF50' if sentiment == 'POSITIVE' else '#F44336'
        ax.barh(dist_df['Model'], dist_df[sentiment], left=bottom_values, color=color, label=sentiment)
        bottom_values += dist_df[sentiment].values
    
    # Add percentages as text
    y_positions = range(len(dist_df))
    x_positions = np.zeros(len(dist_df))
    
    for sentiment in sentiments:
        for i, value in enumerate(dist_df[sentiment]):
            if value > 5:  # Only add text if segment is large enough
                ax.text(x_positions[i] + value/2, y_positions[i], 
                         f"{value:.0f}%", ha='center', va='center', 
                         color='black', fontweight='bold')
            x_positions[i] += value
    
    # Customize plot
    ax.set_xlim(0, 100)
    ax.set_title('Sentiment Distribution for Binary Classification by Model (%) without Context', fontsize=14)
    ax.set_xlabel('Percentage', fontsize=12)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    ax.legend(title='Sentiment')
    
    # Highlight human annotations
    human_idx = list(dist_df['Model']).index('Human Annotator')
    ax.get_yticklabels()[human_idx].set_fontweight('bold')
    ax.get_yticklabels()[human_idx].set_color('blue')
    
    plt.tight_layout()
    plt.savefig('binary_classification_zero_context_sentiment_distribution_by_model.png', dpi=300, bbox_inches='tight')
    plt.close()

# Create the aggregate visualizations
create_agreement_visualization()
create_distribution_visualization()

print("All visualizations have been created successfully.")