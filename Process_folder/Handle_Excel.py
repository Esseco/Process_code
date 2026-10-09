import pandas as pd

def replace_hyphen(df_f, exclude_cols):
    df = pd.read_csv(df_f)
    if isinstance(exclude_cols, str):
        exclude_cols = [exclude_cols]
    ex_col = ['e']
    ex_col.extend(exclude_cols)
    target_cols = [c for c in df.columns if c not in ex_col]
    
    for col in target_cols:
        df[col] = df[col].astype(str).str.replace('-', '_', regex=False)
            
    return df
