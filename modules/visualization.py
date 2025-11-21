import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from io import BytesIO
import base64
import numpy as np

sns.set_style('whitegrid')

def _to_base64(fig):
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{data}"

def generate_charts(df, opts: dict):
    charts = []

    # Detect columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    # -------- FIXED DATE DETECTION --------
    date_col = None

    # First: try detecting already-parsed datetime columns
    date_cols = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()
    if len(date_cols) > 0:
        date_col = date_cols[0]

    # Second: try forcing parse
    if date_col is None:
        for c in df.columns:
            try:
                parsed = pd.to_datetime(df[c], errors='raise')
                df[c] = parsed
                date_col = c
                break
            except:
                pass

    # Prevent sum() on datetime columns:
    if date_col in numeric_cols:
        numeric_cols.remove(date_col)

    # KPIs (Simple cards as bar images)
    if numeric_cols:
        kpi_fig = plt.figure(figsize=(6,3))
        total = df[numeric_cols[0]].sum()
        avg = df[numeric_cols[0]].mean()
        count = df.shape[0]
        plt.bar(["Total", "Average", "Rows"], [total, avg, count])
        plt.title("KPI Summary")
        charts.append({
            'type': 'kpi',
            'title': 'Overview KPIs',
            'image': _to_base64(kpi_fig)
        })

    # Time series charts
    if date_col and numeric_cols:
        fig = plt.figure(figsize=(10,4))
        plt.plot(df[date_col], df[numeric_cols[0]])
        plt.title(f"Trend Over Time: {numeric_cols[0]}")
        plt.xticks(rotation=45)
        charts.append({'type':'time', 'title':'Time Series', 'image':_to_base64(fig)})

        # Moving average
        ma = df.sort_values(date_col)[numeric_cols[0]].rolling(7).mean()
        fig = plt.figure(figsize=(10,4))
        plt.plot(df[date_col], ma)
        plt.title(f"7-Day Moving Average: {numeric_cols[0]}")
        charts.append({'type':'trend', 'title':'Moving Avg', 'image':_to_base64(fig)})

        # Monthly trend
        try:
            df['_month'] = df[date_col].dt.to_period('M')
            monthly = df.groupby('_month')[numeric_cols[0]].sum()
            fig = plt.figure(figsize=(10,4))
            monthly.plot(kind='line')
            plt.title("Monthly Trend")
            charts.append({'type':'monthly','title':'Monthly Trend','image':_to_base64(fig)})
        except:
            pass

    # Top products (if category exists)
    if cat_cols:
        for col in cat_cols[:2]:
            fig = plt.figure(figsize=(8,4))
            df[col].value_counts().head(10).plot(kind='bar')
            plt.title(f"Top categories: {col}")
            charts.append({'type':'category','title':col,'image':_to_base64(fig)})

    # Numeric distros (histograms)
    if numeric_cols:
        for col in numeric_cols[:3]:
            fig = plt.figure(figsize=(7,4))
            sns.histplot(df[col], bins=30, kde=True)
            plt.title(f"Distribution: {col}")
            charts.append({'type':'histogram','title':col,'image':_to_base64(fig)})

    # Boxplots (outlier visualization)
    for col in numeric_cols[:3]:
        fig = plt.figure(figsize=(6,3))
        sns.boxplot(x=df[col])
        plt.title(f"Outlier Boxplot: {col}")
        charts.append({'type':'boxplot','title':col,'image':_to_base64(fig)})

    # Missing-value heatmap
    fig = plt.figure(figsize=(8,4))
    sns.heatmap(df.isnull(), cbar=False)
    plt.title("Missing Value Heatmap")
    charts.append({'type':'missing', 'title':'Missing Values', 'image':_to_base64(fig)})

    # Correlation heatmap
    if len(numeric_cols) > 1:
        fig = plt.figure(figsize=(8,6))
        sns.heatmap(df[numeric_cols].corr(), annot=True, fmt='.2f', cmap='coolwarm')
        plt.title("Correlation Matrix")
        charts.append({'type':'corr','title':'Correlation Heatmap','image':_to_base64(fig)})

    # Scatter plots between numeric columns
    if len(numeric_cols) >= 2:
        fig = plt.figure(figsize=(7,4))
        sns.scatterplot(x=df[numeric_cols[0]], y=df[numeric_cols[1]])
        plt.title(f"Scatter: {numeric_cols[0]} vs {numeric_cols[1]}")
        charts.append({'type':'scatter','title':'Scatter Plot','image':_to_base64(fig)})

    # Scatter + Regression
    if len(numeric_cols) >= 2:
        fig = plt.figure(figsize=(7,4))
        sns.regplot(x=df[numeric_cols[0]], y=df[numeric_cols[1]])
        plt.title(f"Regression: {numeric_cols[0]} vs {numeric_cols[1]}")
        charts.append({'type':'regression','title':'Regression Plot','image':_to_base64(fig)})

    # Pairplot (small datasets only)
    if len(numeric_cols) <= 5 and len(numeric_cols) > 1:
        try:
            g = sns.pairplot(df[numeric_cols])
            g.fig.suptitle("Pairplot Matrix", y=1.02)
            buf = BytesIO()
            g.savefig(buf, format='png')
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode('utf-8')
            charts.append({
                'type': 'pairplot',
                'title': 'Pairplot',
                'image': f"data:image/png;base64,{b64}"
            })
            plt.close()
        except:
            pass

    return charts
