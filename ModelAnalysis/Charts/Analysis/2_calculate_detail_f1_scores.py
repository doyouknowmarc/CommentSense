import pandas as pd
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

# Load the CSV file
#df = pd.read_csv('modified_RESULTS_All_Models_User Evaluation Study - 20 Comments_WITHOUT_context.csv', sep=';')
df = pd.read_csv('modified_RESULTS_All_Models_User Evaluation Study - 20 Comments_with_context.csv', sep=';')

def calculate_model_metrics():
    # Get human annotations as ground truth
    ground_truth = df['(MODUS) Human Annotator']
    
    # Dictionary to store results
    results = []
    
    # Calculate metrics for each model (excluding the human annotator and Comment column)
    for model in df.columns[2:]:
        predictions = df[model]
        
        # Calculate precision, recall, and f1 for each class
        precision, recall, f1, support = precision_recall_fscore_support(
            ground_truth,
            predictions,
            labels=['POSITIVE', 'NEUTRAL', 'NEGATIVE'],
            zero_division=0
        )
        
        # Store results
        results.append({
            'Model': model,
            'Positive_Precision': precision[0],
            'Positive_Recall': recall[0],
            'Positive_F1': f1[0],
            'Positive_Support': support[0],
            'Neutral_Precision': precision[1],
            'Neutral_Recall': recall[1],
            'Neutral_F1': f1[1],
            'Neutral_Support': support[1],
            'Negative_Precision': precision[2],
            'Negative_Recall': recall[2],
            'Negative_F1': f1[2],
            'Negative_Support': support[2],
            'Macro_F1': np.mean(f1)
        })
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    results_df = calculate_model_metrics()
    results_df.to_csv('detailed_f1_scores.csv', index=False)
    print("Results have been saved to 'detailed_f1_scores.csv'")