import pandas as pd
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

# Load the CSV file
df = pd.read_csv('/Users/marc/Documents/GitHub/_MASTER_/GithubUpload/ModelAnalysis/Charts/Analysis/gemma3_modified_RESULTS_All_Models_User Evaluation Study - 20 Comments_with_context.csv', sep=';')

def calculate_model_metrics():
    # Get human annotations as ground truth
    ground_truth = df['(MODUS) Human Annotator']
    
    # Dictionary to store results
    results = {}
    
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
        results[model] = {
            'Positive': {'precision': precision[0], 'recall': recall[0], 'f1': f1[0], 'support': support[0]},
            'Neutral': {'precision': precision[1], 'recall': recall[1], 'f1': f1[1], 'support': support[1]},
            'Negative': {'precision': precision[2], 'recall': recall[2], 'f1': f1[2], 'support': support[2]}
        }
        
        # Calculate weighted averages
        total_support = sum(support)
        weighted_precision = sum(p * s for p, s in zip(precision, support)) / total_support
        weighted_recall = sum(r * s for r, s in zip(recall, support)) / total_support
        weighted_f1 = sum(f * s for f, s in zip(f1, support)) / total_support
        
        results[model]['weighted_avg'] = {
            'precision': weighted_precision,
            'recall': weighted_recall,
            'f1': weighted_f1,
            'total_support': total_support
        }
    
    return results

def print_results(results):
    print("\nWeighted F1 Score Analysis")
    print("=" * 80)
    
    for model, metrics in results.items():
        print(f"\nModel: {model}")
        print("-" * 40)
        
        # Print per-class metrics
        for sentiment in ['Positive', 'Neutral', 'Negative']:
            print(f"\n{sentiment}:")
            print(f"  Precision: {metrics[sentiment]['precision']:.3f}")
            print(f"  Recall: {metrics[sentiment]['recall']:.3f}")
            print(f"  F1: {metrics[sentiment]['f1']:.3f}")
            print(f"  Support: {metrics[sentiment]['support']}")
        
        # Print weighted averages
        print("\nWeighted Averages:")
        print(f"  Precision: {metrics['weighted_avg']['precision']:.3f}")
        print(f"  Recall: {metrics['weighted_avg']['recall']:.3f}")
        print(f"  F1: {metrics['weighted_avg']['f1']:.3f}")
        print(f"  Total Support: {metrics['weighted_avg']['total_support']}")
        print("=" * 80)

if __name__ == "__main__":
    results = calculate_model_metrics()
    print_results(results)
    
    # Save results to CSV
    rows = []
    for model, metrics in results.items():
        row = {
            'Model': model,
            'Weighted_F1': metrics['weighted_avg']['f1'],
            'Positive_F1': metrics['Positive']['f1'],
            'Neutral_F1': metrics['Neutral']['f1'],
            'Negative_F1': metrics['Negative']['f1'],
            'Positive_Support': metrics['Positive']['support'],
            'Neutral_Support': metrics['Neutral']['support'],
            'Negative_Support': metrics['Negative']['support']
        }
        rows.append(row)
    
    results_df = pd.DataFrame(rows)
    results_df.to_csv('weighted_f1_scores_gemma3.csv', index=False)
    print("\nResults have been saved to 'weighted_f1_scores_gemma3.csv'")