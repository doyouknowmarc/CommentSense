import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the CSV file
df = pd.read_csv('/Users/marc/Documents/GitHub/_MASTER_/GithubUpload/weighted_f1_scores_gemma3.csv')

# Set style - using a valid style
plt.style.use('ggplot')  # Changed from 'seaborn' to 'ggplot' which is more widely available
sns.set_palette("husl")

def create_visualizations():
    # 1. Overall Weighted F1 Score Comparison
    plt.figure(figsize=(15, 8))
    
    # Create color array based on score threshold and highlight DistilBERT-sst2 in red
    colors = []
    for i, (model, score) in enumerate(zip(df['Model'], df['Weighted_F1'])):
        if score == 0.713:
            colors.append('red')
        elif score > 0.80:
            colors.append('#1a02f2')
        elif score > 0.714:
            colors.append('#87CEEB')
        else:
            colors.append('#95a5a6')
    
    bars = plt.barh(df['Model'], df['Weighted_F1'], color=colors)
    
    plt.title('Weighted F1 Scores by Model with Context', fontsize=14, pad=20)
    plt.xlabel('Weighted F1 Score')
    
    # Add value labels on the bars
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2,
                f'{width:.3f}', ha='left', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('visualizations/weighted_f1_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Detailed F1 Scores (Positive, Neutral, Negative)
    plt.figure(figsize=(15, 10))
    x = range(len(df['Model']))
    width = 0.25

    plt.barh([i - width for i in x], df['Positive_F1'], width, label='Positive', color='green', alpha=0.7)
    plt.barh([i for i in x], df['Neutral_F1'], width, label='Neutral', color='yellow', alpha=0.7)
    plt.barh([i + width for i in x], df['Negative_F1'], width, label='Negative', color='red', alpha=0.7)

    plt.yticks(x, df['Model'])
    plt.xlabel('F1 Score')
    plt.title('Detailed F1 Scores by Sentiment Class (Weighted Analysis)', fontsize=14, pad=20)
    plt.legend()
    plt.tight_layout()
    plt.savefig('visualizations/detailed_weighted_f1_scores.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Heatmap of F1 Scores
    plt.figure(figsize=(12, 8))
    scores_heatmap = df[['Positive_F1', 'Neutral_F1', 'Negative_F1']]
    sns.heatmap(scores_heatmap.T, annot=True, fmt='.3f', 
                yticklabels=['Positive', 'Neutral', 'Negative'],
                xticklabels=df['Model'], cmap='YlOrRd')
    plt.title('F1 Scores Heatmap by Sentiment (Weighted Analysis)', fontsize=14, pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('visualizations/weighted_f1_scores_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Support Distribution Visualization
    plt.figure(figsize=(15, 10))
    
    # Create a stacked bar chart for support counts
    support_data = df[['Model', 'Positive_Support', 'Neutral_Support', 'Negative_Support']]
    support_data = support_data.set_index('Model')
    
    ax = support_data.plot(kind='barh', stacked=True, figsize=(15, 10), 
                          color=['green', 'yellow', 'red'], alpha=0.7)
    
    plt.title('Support Distribution by Sentiment Class', fontsize=14, pad=20)
    plt.xlabel('Number of Samples')
    plt.legend(title='Sentiment Class')
    
    # Add value labels
    for i, container in enumerate(ax.containers):
        label_name = ['Positive', 'Neutral', 'Negative'][i]
        for j, val in enumerate(container):
            width = val.get_width()
            if width > 0:  # Only add label if the width is greater than 0
                plt.text(val.get_x() + width/2, val.get_y() + val.get_height()/2,
                        f'{int(width)}', ha='center', va='center', 
                        color='black', fontweight='bold', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('visualizations/support_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # Create visualizations directory if it doesn't exist
    import os
    os.makedirs('visualizations', exist_ok=True)
    
    create_visualizations()
    print("Weighted F1 score visualizations have been created in the 'visualizations' directory.")