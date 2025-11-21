def generate_summary(): pass
import pandas as pd
import numpy as np

def _column_summary(series: pd.Series, total_rows: int):
    nulls = int(series.isnull().sum())
    unique = int(series.nunique(dropna=True))
    dtype = str(series.dtype)
    top = None
    if series.dtype == 'object' or pd.api.types.is_categorical_dtype(series):
        top = series.value_counts().head(3).to_dict()

    stats = None
    outliers = None
    if pd.api.types.is_numeric_dtype(series):
        clean = series.dropna()
        if len(clean):
            q1 = np.percentile(clean, 25)
            q3 = np.percentile(clean, 75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = int(((series < lower) | (series > upper)).sum())
            stats = {
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'min': float(series.min()),
                'max': float(series.max()),
                'iqr': float(iqr)
            }

    return {
        'name': series.name,
        'dtype': dtype,
        'null_count': nulls,
        'null_percentage': f"{100.0 * nulls / total_rows:.2f}%" if total_rows else '0.00%',
        'unique': unique,
        'top_values': top,
        'statistics': stats,
        'outliers': outliers
    }

def generate_summary(df: pd.DataFrame):
    rows, cols = df.shape
    size = df.size
    dtypes = df.dtypes.astype(str).to_dict()
    memory = f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
    total_missing = int(df.isnull().sum().sum())
    missing_percentage = f"{100.0 * total_missing / size:.2f}%" if size else '0.00%'
    duplicate_rows = int(df.duplicated().sum())

    columns = [_column_summary(df[c], rows) for c in df.columns]

    # brief insights
    insights = []
    for c in columns:
        if c['null_count'] > 0:
            insights.append(f"Column '{c['name']}' has {c['null_count']} missing values ({c['null_percentage']}).")
        if c.get('outliers') and c['outliers'] > 0:
            insights.append(f"Column '{c['name']}' contains {c['outliers']} potential outliers.")
        if c['dtype'].startswith('object') and c['unique'] > 0 and c['unique'] / max(1, rows) > 0.5:
            insights.append(f"Column '{c['name']}' has high cardinality ({c['unique']} unique).")

    return {
        'shape': {'rows': rows, 'columns': cols},
        'size': int(size),
        'dtypes': dtypes,
        'memory_usage': memory,
        'total_missing': total_missing,
        'missing_percentage': missing_percentage,
        'duplicate_rows': duplicate_rows,
        'columns': columns,
        'insights': insights
    }
