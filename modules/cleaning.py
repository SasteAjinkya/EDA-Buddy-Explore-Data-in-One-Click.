import pandas as pd
import numpy as np


# ---------------------------
# Missing value handler
# ---------------------------
def _fill_with_strategy(df, strategy):
    method = strategy.get('method', 'drop')
    actions = []

    if method == 'drop':
        df = df.dropna()
        return df, {'action': 'drop_na'}

    if method in ('mean', 'median'):
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().any():
                val = df[col].mean() if method == 'mean' else df[col].median()
                df[col].fillna(val, inplace=True)
                actions.append(f"Filled {col} with {method} ({val})")

    elif method == 'mode':
        for col in df.columns:
            if df[col].isnull().any():
                mode_val = df[col].mode()
                if not mode_val.empty:
                    df[col].fillna(mode_val[0], inplace=True)
                    actions.append(f"Filled {col} with mode ({mode_val[0]})")

    elif method == 'constant':
        const = strategy.get('value', '')
        df.fillna(const, inplace=True)
        actions.append(f"Filled all missing with constant value '{const}'")

    elif method == 'ffill':
        df.fillna(method='ffill', inplace=True)
        actions.append('Filled missing with forward fill')

    elif method == 'bfill':
        df.fillna(method='bfill', inplace=True)
        actions.append('Filled missing with backward fill')

    return df, {'actions': actions}


# ---------------------------
# Duplicate remover
# ---------------------------
def _remove_duplicates(df, remove=True):
    removed = 0
    if remove:
        removed = int(df.duplicated().sum())
        df = df.drop_duplicates()
    return df, removed


# ---------------------------
# Drop fully empty columns
# ---------------------------
def _drop_empty_cols(df, drop=True):
    dropped_cols = []
    if drop:
        empty = df.columns[df.isnull().all()].tolist()
        if empty:
            df = df.drop(columns=empty)
            dropped_cols = empty
    return df, dropped_cols


# ---------------------------
# NEW: Outlier remover (IQR)
# ---------------------------
def _remove_outliers(df, remove=True, method='iqr', z_thresh=3.0, cap=False, cap_q=(0.01, 0.99)):
    """
    Remove or cap outliers in numeric columns using a single-pass approach.

    Parameters:
    - df: pandas.DataFrame
    - remove: bool - if True remove outlier rows; if False just return info
    - method: 'iqr' or 'zscore'
    - z_thresh: threshold for z-score method
    - cap: if True, winsorize (cap) values instead of removing rows
    - cap_q: tuple (low_q, high_q) quantiles for capping (e.g. 0.01,0.99)

    Returns:
    - df_out: dataframe after removal/capping
    - info: dict mapping column -> number of outlier rows (based on original df)
    """

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return df, {}

    orig_len = len(df)
    outlier_info = {}

    # compute thresholds on original df (single-pass)
    thresholds = {}
    if method == 'iqr':
        for col in numeric_cols:
            col_nonnull = df[col].dropna()
            if col_nonnull.empty:
                continue
            q1 = col_nonnull.quantile(0.25)
            q3 = col_nonnull.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            thresholds[col] = (lower, upper)
    elif method == 'zscore':
        means = df[numeric_cols].mean()
        stds = df[numeric_cols].std(ddof=0)
        for col in numeric_cols:
            thresholds[col] = (means[col] - z_thresh * stds[col], means[col] + z_thresh * stds[col])
    else:
        raise ValueError("method must be 'iqr' or 'zscore'")


    outlier_mask = pd.Series(False, index=df.index)

    for col, (lower, upper) in thresholds.items():
        # Mark rows where value < lower or value > upper (take care with NaNs)
        mask_col = df[col].notna() & ((df[col] < lower) | (df[col] > upper))
        outlier_info[col] = int(mask_col.sum())
        outlier_mask = outlier_mask | mask_col

    # If no outliers found
    total_outliers = int(outlier_mask.sum())
    if total_outliers == 0:
        return df.copy(), outlier_info

    # If cap (winsorize) is requested, replace extreme values instead of dropping rows
    if cap:
        df_out = df.copy()
        for col, (lower, upper) in thresholds.items():
            if col not in df_out.columns:
                continue
            # compute capping values using quantiles (safer for business)
            low_cap = df_out[col].quantile(cap_q[0])
            high_cap = df_out[col].quantile(cap_q[1])
            df_out[col] = df_out[col].clip(lower=low_cap, upper=high_cap)
        return df_out, outlier_info

    # Otherwise remove rows that are outliers in any column
    df_out = df.loc[~outlier_mask].copy()

    return df_out, outlier_info


def clean_dataframe(df, options: dict):
    """
    Full cleaning pipeline including:
    - duplicates removal
    - drop empty cols
    - missing value handling
    - single-value column drop
    - outlier removal or capping (single-pass)
    Returns cleaned df and a report dict.
    Options:
      options = {
        'remove_duplicates': True,
        'remove_empty_cols': True,
        'missing': {'method':'median'|'mean'|'mode'|'drop'|'constant'|'ffill'|'bfill', 'value': ...},
        'remove_outliers': True,
        'outlier_method': 'iqr' or 'zscore',
        'outlier_cap': False,  # if True, cap instead of drop
        'outlier_z_thresh': 3.0,
        'outlier_cap_q': (0.01,0.99)
      }
    """
    report = {'actions': []}
    before_shape = df.shape

    # 1. Remove duplicates
    remove_dup = options.get('remove_duplicates', True)
    df, removed_dup = _remove_duplicates(df, remove_dup)
    if removed_dup:
        report['actions'].append(f"Removed {removed_dup} duplicate rows")

    # 2. Drop empty columns
    remove_empty = options.get('remove_empty_cols', True)
    df, dropped_cols = _drop_empty_cols(df, remove_empty)
    if dropped_cols:
        report['actions'].append(f"Dropped empty columns: {dropped_cols}")

    # 3. Missing values
    missing_opts = options.get('missing', {'method': 'drop'})
    df, missing_report = _fill_with_strategy(df, missing_opts)
    if 'action' in missing_report and missing_report['action'] == 'drop_na':
        report['actions'].append('Dropped rows with missing values')
    elif 'actions' in missing_report:
        report['actions'].extend(missing_report['actions'])

    # 4. Remove single-value columns
    single_val_cols = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]
    if single_val_cols:
        df = df.drop(columns=single_val_cols)
        report['actions'].append(f"Dropped single-value columns: {single_val_cols}")

    # 5. Outlier handling (single-pass)
    remove_outliers_opt = options.get('remove_outliers', True)
    outlier_method = options.get('outlier_method', 'iqr')
    outlier_cap = options.get('outlier_cap', False)
    z_thresh = options.get('outlier_z_thresh', 3.0)
    cap_q = options.get('outlier_cap_q', (0.01, 0.99))

    df_before_outliers = df.copy()  # for counting if needed
    df, outlier_info = _remove_outliers(
        df,
        remove=remove_outliers_opt and not outlier_cap,
        method=outlier_method,
        z_thresh=z_thresh,
        cap=outlier_cap,
        cap_q=cap_q
    )
    if outlier_info:
        report['actions'].append(f"Outliers handled: {outlier_info} (method={outlier_method}, cap={outlier_cap})")

    # Final summary
    after_shape = df.shape
    report['before'] = {'rows': before_shape[0], 'columns': before_shape[1]}
    report['after'] = {'rows': after_shape[0], 'columns': after_shape[1]}
    report['summary'] = f"{before_shape} → {after_shape}"

    return df, report

