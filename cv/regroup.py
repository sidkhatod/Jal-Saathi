import argparse
import os
import time
import logging
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd
import numpy as np
import networkx as nx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def popcount64(x):
    x = x - ((x >> 1) & 0x5555555555555555)
    x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
    x = (x + (x >> 4)) & 0x0f0f0f0f0f0f0f0f
    x = x + (x >> 8)
    x = x + (x >> 16)
    x = x + (x >> 32)
    return x & 0x7f

def pack_hash(h_list):
    return np.packbits(np.array(h_list), axis=-1).view(np.uint64).squeeze(-1)

def main():
    parser = argparse.ArgumentParser(description="Regroup images from manifest based on new threshold.")
    parser.add_argument('--manifest', type=str, required=True, help="Path to manifest.parquet")
    parser.add_argument('--hash_thresh', type=int, default=8, help="Max Hamming distance to match")
    parser.add_argument('--output', type=str, default=None, help="Output parquet path (default: overwrite)")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        logging.error(f"Manifest not found: {manifest_path}")
        return

    out_path = args.output if args.output else str(manifest_path)

    logging.info(f"Loading manifest: {manifest_path}")
    t0 = time.time()
    table = pq.read_table(str(manifest_path))
    df = table.to_pandas()
    
    if df.empty:
        logging.info("Empty manifest.")
        return
        
    N = len(df)
    
    p_hashes_packed = np.zeros((N, 8), dtype=np.uint64)
    d_hashes_packed = np.zeros((N, 8), dtype=np.uint64)
    
    for i, row in df.iterrows():
        p_list = [np.unpackbits(np.array([int(h[idx:idx+2], 16) for idx in range(0, 16, 2)], dtype=np.uint8)) for h in row['phash_variants'].split(',')]
        d_list = [np.unpackbits(np.array([int(h[idx:idx+2], 16) for idx in range(0, 16, 2)], dtype=np.uint8)) for h in row['dhash_variants'].split(',')]
        p_hashes_packed[i] = pack_hash(p_list)
        d_hashes_packed[i] = pack_hash(d_list)
        
    logging.info(f"Regrouping {N} images at threshold {args.hash_thresh}...")
    G = nx.Graph()
    G.add_nodes_from(range(N))
    
    batch_size = 1000
    for i in range(0, N, batch_size):
        end_i = min(i + batch_size, N)
        p_batch = p_hashes_packed[i:end_i]
        d_batch = d_hashes_packed[i:end_i]
        
        for j in range(i + 1, N):
            p_xor = p_batch ^ p_hashes_packed[j, 0]
            d_xor = d_batch ^ d_hashes_packed[j, 0]
            
            p_dist = popcount64(p_xor).min(axis=-1)
            d_dist = popcount64(d_xor).min(axis=-1)
            dist = np.maximum(p_dist, d_dist)
            
            matches = np.where(dist <= args.hash_thresh)[0]
            for k in matches:
                G.add_edge(i + k, j)
                
    components = list(nx.connected_components(G))
    new_group_ids = np.zeros(N, dtype=np.int64)
    for group_id, comp in enumerate(components):
        for node in comp:
            new_group_ids[node] = group_id
            
    df['group_id'] = new_group_ids
    unique_groups = len(components)
    
    t1 = time.time()
    logging.info(f"Regrouping complete in {t1-t0:.2f}s. Found {unique_groups} unique groups.")
    
    table_new = pa.Table.from_pandas(df)
    pq.write_table(table_new, out_path)
    logging.info(f"Saved updated manifest to {out_path}")

if __name__ == '__main__':
    main()
