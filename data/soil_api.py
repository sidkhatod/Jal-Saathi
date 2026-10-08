import os
import duckdb
import pandas as pd
from config import N_MIN

def get_soil_rating(district_code: str, block_code: str = None, village_code: str = None):
    base_dir = os.path.dirname(__file__)
    
    def query_level(level_name, code_filters):
        path = os.path.join(base_dir, 'processed', f'soil_haryana_{level_name}.parquet')
        if not os.path.exists(path): return None
        where_clause = " AND ".join(code_filters)
        q = f"SELECT nutrient_name, nutrient_level, year, n_samples FROM '{path}' WHERE {where_clause}"
        return duckdb.query(q).df()
        
    levels = []
    if village_code and block_code:
        levels.append(('village', [f"district_code = '{district_code}'", f"block_code = '{block_code}'", f"village_code = '{village_code}'"]))
    if block_code:
        levels.append(('block', [f"district_code = '{district_code}'", f"block_code = '{block_code}'"]))
    levels.append(('district', [f"district_code = '{district_code}'"]))
    
    dfs = []
    for l_name, filters in levels:
        df = query_level(l_name, filters)
        if df is not None and not df.empty:
            df['level_used'] = l_name
            dfs.append(df)
            
    if not dfs:
        return {}
        
    res = pd.concat(dfs)
    
    totals = res.groupby(['nutrient_name', 'year', 'level_used'])['n_samples'].sum().reset_index()
    totals = totals.rename(columns={'n_samples': 'total_samples'})
    
    res = res.merge(totals, on=['nutrient_name', 'year', 'level_used'])
    
    # Filter by N_MIN (except for district which is fallback)
    res = res[(res['level_used'] == 'district') | (res['total_samples'] >= N_MIN)]
    
    level_order = {'village': 1, 'block': 2, 'district': 3}
    res['level_rank'] = res['level_used'].map(level_order)
    
    res = res.sort_values(['nutrient_name', 'level_rank', 'year'], ascending=[True, True, False])
    
    out = {}
    for nutrient in res['nutrient_name'].unique():
        n_df = res[res['nutrient_name'] == nutrient]
        best_row = n_df.iloc[0]
        best_level_used = best_row['level_used']
        best_year = best_row['year']
        
        dist_df = n_df[(n_df['level_used'] == best_level_used) & (n_df['year'] == best_year)]
        
        dist = {}
        dominant_level = None
        max_s = -1
        for _, r in dist_df.iterrows():
            lvl = r['nutrient_level']
            s = int(r['n_samples'])
            dist[lvl] = s
            if s > max_s:
                max_s = s
                dominant_level = lvl
                
        out[nutrient] = {
            "dominant_level": dominant_level,
            "distribution": dist,
            "level_used": best_level_used,
            "year_used": best_year,
            "n_samples": int(best_row['total_samples'])
        }
        
    return out
