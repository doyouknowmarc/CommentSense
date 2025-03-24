import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Read the data
df = pd.read_csv('../ModelAnalysis/Charts/Analysis/Binary_Classification/binary_detailed_f1_scores_without_context.csv')

def create_detailed_heatmap():
    # Create a directory for the heatmap
    import os
    os.makedirs('heatmap_visualizations', exist_ok=True)
    
    # Prepare the data for the heatmap
    metrics_columns = [
        'Positive_Precision', 'Positive_Recall', 'Positive_F1',
        'Negative_Precision', 'Negative_Recall', 'Negative_F1',
        'Macro_F1'
    ]
    
    # Create the heatmap data
    heatmap_data = df[metrics_columns].copy()
    heatmap_data.index = df['Model']
    
    # Rename columns for better visualization
    column_names = {
        'Positive_Precision': 'Pos Prec',
        'Positive_Recall': 'Pos Rec',
        'Positive_F1': 'Pos F1',
        'Negative_Precision': 'Neg Prec',
        'Negative_Recall': 'Neg Rec',
        'Negative_F1': 'Neg F1',
        'Macro_F1': 'Macro F1'
    }
    heatmap_data.columns = [column_names[col] for col in heatmap_data.columns]
    
    # Create the figure with larger size
    plt.figure(figsize=(15, 12))
    
    # Create heatmap
    sns.heatmap(heatmap_data, 
                annot=True,
                fmt='.3f',
                cmap='YlOrRd',
                center=0.5,
                vmin=0,
                vmax=1,
                cbar_kws={'label': 'Score'})
    
    plt.title('Detailed Performance Metrics Heatmap without Context', pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the heatmap
    plt.savefig('heatmap_visualizations/detailed_metrics_heatmap.png', 
                dpi=300, 
                bbox_inches='tight')
    plt.close()
    
    print("Heatmap has been created in the 'heatmap_visualizations' directory.")

if __name__ == "__main__":
    create_detailed_heatmap()