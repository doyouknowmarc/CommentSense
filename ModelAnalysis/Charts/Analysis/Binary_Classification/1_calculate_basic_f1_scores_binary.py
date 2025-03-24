import pandas as pd
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

# Load the CSV file
#df = pd.read_csv('../ModelAnalysis/Charts/Analysis/Binary_Classification/with_context/binary-classification-with-context.csv', sep=';')
df = pd.read_csv('../ModelAnalysis/Charts/Analysis/Binary_Classification/with_context/binary-classification-with-context.csv', sep=';')

def calculate_model_metrics():
    # Get human annotations as ground truth
    ground_truth = df['Human Annotator']
    
    # Dictionary to store results
    results = {}
    
    # Calculate metrics for each model (excluding the human annotator and Comment column)
    for model in df.columns[2:]:
        predictions = df[model]
        
        # Calculate precision, recall, and f1 for each class
        precision, recall, f1, support = precision_recall_fscore_support(
            ground_truth,
            predictions,
            labels=['POSITIVE', 'NEGATIVE'],
            zero_division=0
        )
        
        # Store results
        results[model] = {
            'Positive': {'precision': precision[0], 'recall': recall[0], 'f1': f1[0], 'support': support[0]},
            'Negative': {'precision': precision[1], 'recall': recall[1], 'f1': f1[1], 'support': support[1]}
        }
        
        # Calculate macro averages
        results[model]['macro_avg'] = {
            'precision': np.mean(precision),
            'recall': np.mean(recall),
            'f1': np.mean(f1)
        }
    
    return results

def print_results(results):
    print("\nF1 Score Analysis")
    print("=" * 80)
    
    for model, metrics in results.items():
        print(f"\nModel: {model}")
        print("-" * 40)
        
        # Print per-class metrics
        for sentiment in ['Positive', 'Negative']:
            print(f"\n{sentiment}:")
            print(f"  Precision: {metrics[sentiment]['precision']:.3f}")
            print(f"  Recall: {metrics[sentiment]['recall']:.3f}")
            print(f"  F1: {metrics[sentiment]['f1']:.3f}")
            print(f"  Support: {metrics[sentiment]['support']}")
        
        # Print macro averages
        print("\nMacro Averages:")
        print(f"  Precision: {metrics['macro_avg']['precision']:.3f}")
        print(f"  Recall: {metrics['macro_avg']['recall']:.3f}")
        print(f"  F1: {metrics['macro_avg']['f1']:.3f}")
        print("=" * 80)

if __name__ == "__main__":
    results = calculate_model_metrics()
    print_results(results)
    
    # Optionally save results to CSV
    rows = []
    for model, metrics in results.items():
        row = {
            'Model': model,
            'Macro_F1': metrics['macro_avg']['f1'],
            'Positive_F1': metrics['Positive']['f1'],
            'Negative_F1': metrics['Negative']['f1']
        }
        rows.append(row)
    
    results_df = pd.DataFrame(rows)

    #results_df.to_csv('macro_f1_scores_binary-classification_with_context.csv', index=False)
    #print("\nResults have been saved to 'macro_f1_scores_binary-classification_with_context.csv'")

    results_df.to_csv('macro_f1_scores_binary-classification_zero_context.csv', index=False)
    print("\nResults have been saved to 'macro_f1_scores_binary-classification_zero_context.csv'")