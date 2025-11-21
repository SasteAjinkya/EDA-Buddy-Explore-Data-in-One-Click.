import pandas as pd

def extract_features(df: pd.DataFrame):
    numeric = df.select_dtypes(include='number').columns.tolist()
    categorical = df.select_dtypes(include=['object','category']).columns.tolist()
    datetime = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    strong_corrs = []
    if len(numeric) > 1:
        corr = df[numeric].corr()
        for i in range(len(corr.columns)):
            for j in range(i+1, len(corr.columns)):
                val = corr.iloc[i,j]
                if abs(val) > 0.7:
                    strong_corrs.append({'f1': corr.columns[i], 'f2': corr.columns[j], 'corr': float(val)})

    suggestions = []
    for c in categorical:
        uniq = df[c].nunique()
        if uniq / max(1, len(df)) > 0.5:
            suggestions.append(f"Column '{c}' has high cardinality: {uniq}")

    return {
        'numeric_features': numeric,
        'categorical_features': categorical,
        'datetime_features': datetime,
        'strong_correlations': strong_corrs,
        'suggestions': suggestions
    }

