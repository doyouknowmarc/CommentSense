import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the CSV file
df = pd.read_csv('../ModelAnalysis/Charts/Analysis/Best_Model_Data_20_Comments_WITHOUT_context_with_reasoning.csv', sep=';')

# Extract model names and their metrics
models = ['phi4', 'phi3.5', 'qwen2.5:7b', 'qwen2.5:3b']
#models = ['phi4', 'phi3.5', 'mistral-small:22b', 'qwen2.5:7b']
metrics = ['Total Duration', 'Load Duration', 'Prompt Eval Count', 'Prompt Eval Duration', 'Eval Count', 'Eval Duration']

# Create comparison dataframes
performance_data = {}
sentiment_data = {}

for model in models:
    # Get performance metrics
    model_metrics = {}
    for metric in metrics:
        column_name = f"{model} - {metric}"
        model_metrics[metric] = df[column_name].mean()
    performance_data[model] = model_metrics
    
    # Get sentiment distribution
    sentiment_column = f"{model} - Sentiment"
    sentiment_counts = df[sentiment_column].value_counts()
    sentiment_data[model] = sentiment_counts

# Convert to DataFrames
performance_df = pd.DataFrame(performance_data).T
sentiment_df = pd.DataFrame({model: sentiment_data[model] for model in models})

# Plotting
plt.style.use('seaborn')
fig = plt.figure(figsize=(20, 12))

# 1. Performance Metrics Comparison
ax1 = plt.subplot(2, 2, 1)
performance_df[['Total Duration', 'Load Duration', 'Prompt Eval Duration', 'Eval Duration']].plot(kind='bar', ax=ax1)
plt.title('Duration Metrics Comparison')
plt.xticks(rotation=45)
plt.ylabel('Seconds')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# 2. Count Metrics Comparison
ax2 = plt.subplot(2, 2, 2)
performance_df[['Prompt Eval Count', 'Eval Count']].plot(kind='bar', ax=ax2)
plt.title('Count Metrics Comparison')
plt.xticks(rotation=45)
plt.ylabel('Count')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# 3. Sentiment Distribution
ax3 = plt.subplot(2, 1, 2)
sentiment_proportions = pd.DataFrame({
    model: sentiment_data[model] / sentiment_data[model].sum() * 100
    for model in models
})
sentiment_proportions.plot(kind='bar', stacked=True, ax=ax3)
plt.title('Sentiment Distribution Comparison')
plt.xticks(rotation=45)
plt.ylabel('Percentage')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.show()

# Print detailed statistics
print("\nPerformance Metrics Summary:")
print(performance_df.round(2))
print("\nSentiment Distribution Summary:")
print(sentiment_df.fillna(0).astype(int))