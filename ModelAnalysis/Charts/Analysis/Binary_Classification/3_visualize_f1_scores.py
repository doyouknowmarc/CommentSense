import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the CSV file
#df = pd.read_csv('../macro_f1_scores_binary-classification_with_context.csv')
df = pd.read_csv('../macro_f1_scores_binary-classification_zero_context.csv')


# Sort the dataframe by Macro_F1 score in ascending order
df = df.sort_values(by='Macro_F1', ascending=True)

# Set style
plt.style.use('seaborn')
sns.set_palette("husl")

def create_visualizations():
    # 1. Overall Macro F1 Score Comparison
    plt.figure(figsize=(15, 8))
    
    # Create color array based on score threshold
    colors = ['#FF0000' if model == 'DistilBERT-sst2' else '#1a02f2' if score > 0.40 else '#95a5a6' 
              for model, score in zip(df['Model'], df['Macro_F1'])]
    bars = plt.barh(df['Model'], df['Macro_F1'], color=colors)
    
    plt.title('Macro F1 Scores for Binary Classification by Model without Context', fontsize=14, pad=20)
    plt.xlabel('Macro F1 Score')
    
    # Add value labels on the bars
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2,
                f'{width:.3f}', ha='left', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('visualizations/macro_f1_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Detailed F1 Scores (Positive, Neutral, Negative)
    plt.figure(figsize=(15, 10))
    x = range(len(df['Model']))
    width = 0.25

    plt.barh([i - width for i in x], df['Positive_F1'], width, label='Positive', color='green', alpha=0.7)
    plt.barh([i + width for i in x], df['Negative_F1'], width, label='Negative', color='red', alpha=0.7)

    plt.yticks(x, df['Model'])
    plt.xlabel('F1 Score')
    plt.title('Detailed F1 Scores by Sentiment Class with Context', fontsize=14, pad=20)
    plt.legend()
    plt.tight_layout()
    plt.savefig('visualizations/detailed_f1_scores.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Heatmap of F1 Scores
    plt.figure(figsize=(12, 8))
    scores_heatmap = df[['Positive_F1', 'Negative_F1']]
    sns.heatmap(scores_heatmap.T, annot=True, fmt='.3f', 
                yticklabels=['Positive', 'Negative'],
                xticklabels=df['Model'], cmap='YlOrRd')
    plt.title('F1 Scores Heatmap Sentiment with Context', fontsize=14, pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('visualizations/f1_scores_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # Create visualizations directory if it doesn't exist
    import os
    os.makedirs('visualizations', exist_ok=True)
    
    create_visualizations()
    print("Visualizations have been created in the 'visualizations' directory.")