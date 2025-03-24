import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Read the CSV file

df = pd.read_csv('../ModelAnalysis/Charts/Analysis/Binary_Classification/without_context/adjusted_for_binary_classification_WITHOUT_context.csv', sep=';')

# Create output directory for plots
import os
os.makedirs('visualization_outputs', exist_ok=True)

# 1. Heatmap of Model Agreement
plt.figure(figsize=(15, 10))
model_columns = df.columns[1:]  # Skip 'Comment' column
agreement_matrix = pd.DataFrame(index=model_columns, columns=model_columns, dtype=float)  # Specify dtype

for model1 in model_columns:
    for model2 in model_columns:
        agreement = (df[model1] == df[model2]).mean()
        agreement_matrix.loc[model1, model2] = float(agreement)  # Explicit conversion to float

# Convert the entire matrix to float
agreement_matrix = agreement_matrix.astype(float)

sns.heatmap(agreement_matrix, annot=True, cmap='YlOrRd', fmt='.2f')
plt.title('Model Agreement Heatmap without Context')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig('visualization_outputs/model_agreement_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Sentiment Distribution per Model
plt.figure(figsize=(15, 8))
model_sentiment_counts = pd.DataFrame()

for model in model_columns:
    counts = df[model].value_counts()
    model_sentiment_counts[model] = counts

model_sentiment_counts = model_sentiment_counts.fillna(0)
model_sentiment_counts.plot(kind='bar', stacked=True)
plt.title('Sentiment Distribution Across Models')
plt.xlabel('Sentiment')
plt.ylabel('Count')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('visualization_outputs/sentiment_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Agreement with Human Annotator
human_agreement = pd.Series(index=model_columns)
human_column = '(MODUS) Human Annotator'

for model in model_columns:
    if model != human_column:
        agreement = (df[model] == df[human_column]).mean()
        human_agreement[model] = agreement

plt.figure(figsize=(12, 6))
human_agreement.sort_values(ascending=True).plot(kind='barh')
plt.title('Model Agreement with Human Annotator')
plt.xlabel('Agreement Rate')
plt.tight_layout()
plt.savefig('visualization_outputs/human_agreement.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Sentiment Consistency Across Comments
consistency_matrix = pd.DataFrame(index=df['Comment'], columns=['Agreement_Rate'])

for idx, row in df.iterrows():
    # Calculate the most common sentiment for this comment
    sentiments = row[1:].value_counts()
    max_agreement = sentiments.iloc[0] / len(row[1:])
    consistency_matrix.loc[row['Comment'], 'Agreement_Rate'] = max_agreement

plt.figure(figsize=(10, 6))
consistency_matrix.sort_values('Agreement_Rate').plot(kind='barh')
plt.title('Sentiment Consistency Across Models per Comment')
plt.xlabel('Agreement Rate')
plt.tight_layout()
plt.savefig('visualization_outputs/comment_consistency.png', dpi=300, bbox_inches='tight')
plt.close()

print("All visualizations have been generated in the 'visualization_outputs' directory!")