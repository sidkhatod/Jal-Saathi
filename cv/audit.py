import os
import sys
import glob
import json
import yaml
import logging
from pathlib import Path
from collections import defaultdict, Counter
import argparse
import math

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import networkx as nx
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import imagehash
import numpy as np
import matplotlib.pyplot as plt



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_d4_variants(img):
    """Returns the 8 D4 dihedral group symmetry variants of a PIL image."""
    return [
        img,
        img.rotate(90, expand=True),
        img.rotate(180, expand=True),
        img.rotate(270, expand=True),
        img.transpose(Image.FLIP_LEFT_RIGHT),
        img.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True),
        img.transpose(Image.FLIP_LEFT_RIGHT).rotate(180, expand=True),
        img.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True),
    ]

def scan_folder_tree(data_root, depth=2):
    """Scan folder tree up to a certain depth."""
    root_path = Path(data_root)
    tree = defaultdict(list)
    if not root_path.exists():
        return tree
    
    for path in root_path.rglob('*'):
        if path.is_dir():
            rel_parts = path.relative_to(root_path).parts
            if len(rel_parts) <= depth:
                parent = str(Path(*rel_parts[:-1])) if len(rel_parts) > 1 else str(rel_parts[0] if rel_parts else "")
                if parent:
                    tree[parent].append(rel_parts[-1])
                elif rel_parts:
                    tree["root"].append(rel_parts[-1])
    # deduplicate lists
    for k in tree:
        tree[k] = list(set(tree[k]))
    return dict(tree)

def is_image(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']

def process_image(full_path, rel_path, class_map):
    """Open image, get stats, compute hashes."""
    dataset = rel_path.parts[0] if len(rel_path.parts) > 0 else "unknown"
    raw_label = rel_path.parent.name
    canonical_label = class_map.get(raw_label, None)
    
    is_heldout = dataset.lower() in ['nwrd', 'nwrd_wheat_rust', 'nwrd wheat rust', 'riceleafbd']
    
    record = {
        'relative_path': str(rel_path),
        'dataset': dataset,
        'raw_label': raw_label,
        'canonical_label': canonical_label,
        'group_id': -1,
        'width': -1,
        'height': -1,
        'phash': None,
        'dhash': None,
        'phash_variants': None,
        'dhash_variants': None,
        'is_heldout_field_set': is_heldout,
        'valid': False,
        'format': None,
        'rust_pixel_pct': None
    }
    
    try:
        with Image.open(full_path) as img:
            img_format = img.format
            record['format'] = img_format
            img = img.convert('RGB')
            record['width'], record['height'] = img.size
            record['valid'] = True
            
            # Compute hashes for 8 D4 variants
            variants = get_d4_variants(img)
            # Use fixed size for hashing to speed up
            variants_small = [v.resize((256, 256), Image.Resampling.LANCZOS) for v in variants]
            
            record['phash_variants'] = ",".join(str(imagehash.phash(v)) for v in variants_small)
            record['dhash_variants'] = ",".join(str(imagehash.dhash(v)) for v in variants_small)
            
            # Use the first variant's phash as the canonical phash for the parquet
            record['phash'] = str(imagehash.phash(variants_small[0]))
            record['dhash'] = str(imagehash.dhash(variants_small[0]))
            
    except Exception as e:
        pass

    return record

def process_nwrd_masks(data_root, valid_records):
    """Pair NWRD images with masks and compute rust %."""
    root_path = Path(data_root)
    # Search for anything named 'masks' or similar
    mask_files = list(root_path.rglob('mask*/*.*')) + list(root_path.rglob('Mask*/*.*'))
    mask_dict = {m.stem: m for m in mask_files if is_image(m.name)}
    
    for r in valid_records:
        if r['dataset'].lower() in ['nwrd', 'nwrd_wheat_rust', 'nwrd wheat rust']:
            stem = Path(r['relative_path']).stem
            if stem in mask_dict:
                try:
                    with Image.open(mask_dict[stem]) as m_img:
                        m_img = m_img.convert('L')
                        m_arr = np.array(m_img)
                        # Assume foreground > 127
                        rust_pixels = np.sum(m_arr > 127)
                        total_pixels = m_arr.size
                        r['rust_pixel_pct'] = (rust_pixels / total_pixels) * 100
                except:
                    pass

def compute_group_ids(records, hash_threshold=4, use_embeddings=True, embed_threshold=0.97):
    """Cluster images using hashes and optionally embeddings."""
    logging.info("Building graph for clustering...")
    G = nx.Graph()
    valid_records = [r for r in records if r['valid']]
    
    for i, r in enumerate(valid_records):
        G.add_node(i)

    N = len(valid_records)
    if N == 0:
        return {}, [], []
        
    logging.info(f"Computing hash distances for {N} images...")
    
    def pack_hash(h_list):
        return np.packbits(np.array(h_list), axis=-1).view(np.uint64).squeeze(-1)
        
    p_hashes_packed = np.zeros((N, 8), dtype=np.uint64)
    d_hashes_packed = np.zeros((N, 8), dtype=np.uint64)
    
    for i, r in enumerate(valid_records):
        # Convert hex strings back to numpy arrays for packing
        p_list = [np.unpackbits(np.array([int(h[idx:idx+2], 16) for idx in range(0, 16, 2)], dtype=np.uint8)) for h in r['phash_variants'].split(',')]
        d_list = [np.unpackbits(np.array([int(h[idx:idx+2], 16) for idx in range(0, 16, 2)], dtype=np.uint8)) for h in r['dhash_variants'].split(',')]
        p_hashes_packed[i] = pack_hash(p_list)
        d_hashes_packed[i] = pack_hash(d_list)

    batch_size = 1000
    
    def popcount64(x):
        x = x - ((x >> 1) & 0x5555555555555555)
        x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
        x = (x + (x >> 4)) & 0x0f0f0f0f0f0f0f0f
        x = x + (x >> 8)
        x = x + (x >> 16)
        x = x + (x >> 32)
        return x & 0x7f

    edges_at_thresh = {t: [] for t in [2, 4, 6, 8, 10]}
    nn_dist = np.full(N, 64, dtype=np.int32)
    near_thresh_pairs = []

    for i in range(0, N, batch_size):
        end_i = min(i + batch_size, N)
        p_batch = p_hashes_packed[i:end_i] # (B, 8)
        d_batch = d_hashes_packed[i:end_i]
        
        for j in range(i + 1, N):
            p_xor = p_batch ^ p_hashes_packed[j, 0]
            d_xor = d_batch ^ d_hashes_packed[j, 0]
            
            p_dist = popcount64(p_xor).min(axis=-1)
            d_dist = popcount64(d_xor).min(axis=-1)
            dist = np.maximum(p_dist, d_dist)
            
            for k in range(end_i - i):
                idx = i + k
                if idx == j: continue
                d = dist[k]
                if d < nn_dist[idx]: nn_dist[idx] = d
                if d < nn_dist[j]: nn_dist[j] = d
                
                for t in [2, 4, 6, 8, 10]:
                    if d <= t:
                        edges_at_thresh[t].append((idx, j))
                
                if d <= hash_threshold:
                    G.add_edge(idx, j)
                if hash_threshold - 2 <= d <= hash_threshold + 2:
                    near_thresh_pairs.append((idx, j, d))

    if use_embeddings:
        import torch
        from torchvision import transforms, models
        import torch.nn.functional as F
        
        logging.info("Extracting embeddings using mobilenet_v3_small...")
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        model.classifier = torch.nn.Identity() # remove classification head
        model = model.to(device).eval()
        
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        embeddings = []
        with torch.no_grad():
            for i, r in enumerate(valid_records):
                try:
                    img = Image.open(r['relative_path']).convert('RGB')
                    t_img = transform(img).unsqueeze(0).to(device)
                    emb = model(t_img).cpu().numpy().flatten()
                    embeddings.append(emb)
                except:
                    embeddings.append(np.zeros(576))
                    
        embeddings = np.array(embeddings)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms
        
        logging.info("Computing embedding similarities...")
        for i in range(0, N, batch_size):
            end_i = min(i + batch_size, N)
            sim = np.dot(embeddings[i:end_i], embeddings.T)
            matches = np.argwhere(sim > embed_threshold)
            for m in matches:
                if m[0] + i < m[1]: 
                    G.add_edge(m[0] + i, m[1])

    logging.info("Extracting connected components...")
    components = list(nx.connected_components(G))
    for group_id, comp in enumerate(components):
        for node in comp:
            valid_records[node]['group_id'] = group_id
            
    group_counts = {}
    for t in [2, 4, 6, 8, 10]:
        Gt = nx.Graph()
        Gt.add_nodes_from(range(N))
        Gt.add_edges_from(edges_at_thresh[t])
        group_counts[t] = nx.number_connected_components(Gt)
        
    return group_counts, nn_dist, near_thresh_pairs

def load_class_map(yaml_path):
    if not os.path.exists(yaml_path):
        return {}
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('folder_mapping', {})

def generate_contact_sheet(records, output_path, samples_per_class=8):
    logging.info("Generating contact sheet...")
    class_images = defaultdict(list)
    for r in records:
        if r['valid'] and r['canonical_label'] is not None:
            class_images[r['canonical_label']].append(r['relative_path'])
            
    if not class_images:
        return

    classes = list(class_images.keys())
    num_classes = len(classes)
    
    img_w, img_h = 200, 200
    margin = 10
    text_h = 30
    
    sheet_w = samples_per_class * (img_w + margin) + margin
    sheet_h = num_classes * (img_h + margin + text_h) + margin
    
    sheet = Image.new('RGB', (sheet_w, sheet_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        
    y_offset = margin
    for cls in sorted(classes):
        draw.text((margin, y_offset), str(cls), fill=(0, 0, 0), font=font)
        y_offset += text_h
        
        paths = class_images[cls]
        sampled = paths[:samples_per_class]
        
        x_offset = margin
        for path in sampled:
            try:
                img = Image.open(path).convert('RGB')
                img = img.resize((img_w, img_h), Image.Resampling.LANCZOS)
                sheet.paste(img, (x_offset, y_offset))
            except:
                pass
            x_offset += img_w + margin
            
        y_offset += img_h + margin
        
    sheet.save(output_path)

def generate_cluster_samples(records, near_thresh_pairs, output_path):
    logging.info("Generating cluster samples...")
    valid_records = [r for r in records if r['valid']]
    
    # 10 largest clusters
    groups = defaultdict(list)
    for i, r in enumerate(valid_records):
        groups[r['group_id']].append(i)
        
    largest_groups = sorted(groups.values(), key=len, reverse=True)[:10]
    
    # sort near_thresh_pairs to get distinct ones near threshold
    near_thresh_pairs = sorted(near_thresh_pairs, key=lambda x: x[2])
    # pick 10 distinct pairs
    selected_pairs = []
    seen = set()
    for u, v, d in near_thresh_pairs:
        if u not in seen and v not in seen:
            selected_pairs.append((u, v, d))
            seen.add(u)
            seen.add(v)
        if len(selected_pairs) == 10:
            break
            
    img_w, img_h = 150, 150
    margin = 10
    text_h = 30
    
    sheet_w = max(6 * (img_w + margin) + margin, 3 * (img_w + margin) + margin)
    sheet_h = 20 * (img_h + margin + text_h) + margin
    
    sheet = Image.new('RGB', (sheet_w, sheet_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        
    y_offset = margin
    draw.text((margin, y_offset), "10 Largest Clusters (up to 6 images)", fill=(0, 0, 0), font=font)
    y_offset += text_h
    
    for g in largest_groups:
        x_offset = margin
        for idx in g[:6]:
            try:
                img = Image.open(valid_records[idx]['relative_path']).convert('RGB')
                img = img.resize((img_w, img_h), Image.Resampling.LANCZOS)
                sheet.paste(img, (x_offset, y_offset))
            except:
                pass
            x_offset += img_w + margin
        y_offset += img_h + margin
        
    draw.text((margin, y_offset), "10 Pairs Near Threshold", fill=(0, 0, 0), font=font)
    y_offset += text_h
    
    for u, v, d in selected_pairs:
        draw.text((margin, y_offset + img_h // 2), f"Dist: {d}", fill=(0, 0, 0), font=font)
        x_offset = margin + 100
        for idx in [u, v]:
            try:
                img = Image.open(valid_records[idx]['relative_path']).convert('RGB')
                img = img.resize((img_w, img_h), Image.Resampling.LANCZOS)
                sheet.paste(img, (x_offset, y_offset))
            except:
                pass
            x_offset += img_w + margin
        y_offset += img_h + margin
        
    # Crop to actual height
    sheet = sheet.crop((0, 0, sheet_w, min(y_offset, sheet_h)))
    sheet.save(output_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_root', type=str, default=os.environ.get('DATA_ROOT', '/kaggle/input'))
    parser.add_argument('--class_map', type=str, default='cv/class_map.yaml')
    parser.add_argument('--output_dir', type=str, default='cv')
    parser.add_argument('--hash_thresh', type=int, default=8)
    parser.add_argument('--use_embed', action='store_true')
    parser.add_argument('--embed_thresh', type=float, default=0.97)
    args = parser.parse_args()
    
    import importlib.util
    if args.use_embed:
        if not (os.path.exists("/kaggle/working") or "SM_MODEL_DIR" in os.environ or importlib.util.find_spec("google.colab")):
            print("Training runs on Kaggle/AWS only")
            sys.exit(2)
    
    data_root = Path(args.data_root)
    if not data_root.exists():
        logging.error(f"Data root {data_root} does not exist.")
        return

    class_map = load_class_map(args.class_map)
    
    import time
    t_start = time.time()
    timings = {}
    
    logging.info("Scanning dataset tree...")
    t0 = time.time()
    tree = scan_folder_tree(data_root)
    timings['scan_folder_tree'] = round(time.time() - t0, 2)
    
    logging.info("Processing images...")
    t0 = time.time()
    records = []
    unreadable = []
    formats = Counter()
    size_dist = []
    
    for root, dirs, files in os.walk(data_root):
        for f in files:
            if is_image(f):
                full_path = Path(root) / f
                
                if any('mask' in p.lower() for p in full_path.parts):
                    continue
                    
                try:
                    rel_path = full_path.relative_to(data_root)
                except ValueError:
                    rel_path = full_path
                    
                rec = process_image(full_path, rel_path, class_map)
                rec['relative_path'] = str(full_path) 
                
                if rec['valid']:
                    formats[rec['format']] += 1
                    size_dist.append((rec['width'], rec['height']))
                else:
                    unreadable.append(str(rel_path))
                records.append(rec)

    logging.info(f"Found {len(records)} images. {len(unreadable)} unreadable.")
    timings['process_images'] = round(time.time() - t0, 2)
    
    t0 = time.time()
    process_nwrd_masks(data_root, records)
    timings['process_nwrd_masks'] = round(time.time() - t0, 2)
    
    t0 = time.time()
    group_counts, nn_dist, near_thresh_pairs = compute_group_ids(records, args.hash_thresh, args.use_embed, args.embed_thresh)
    timings['compute_group_ids'] = round(time.time() - t0, 2)
    
    # Analytics
    df = pd.DataFrame(records)
    
    if df.empty or 'valid' not in df.columns:
        logging.warning("No valid images found.")
        return

    valid_df = df[df['valid'] == True]
    stats_df = valid_df.groupby('canonical_label').agg(
        raw_image_count=('relative_path', 'count'),
        unique_source_groups=('group_id', 'nunique')
    ).reset_index()
    
    leaked_groups = set()
    for g in valid_df['group_id'].unique():
        if g == -1: continue
        group_df = valid_df[valid_df['group_id'] == g]
        if group_df['is_heldout_field_set'].nunique() > 1:
            leaked_groups.add(g)
            
    leaked_test_images = valid_df[(valid_df['is_heldout_field_set'] == True) & (valid_df['group_id'].isin(leaked_groups))].shape[0]
    
    nwrd_df = valid_df[valid_df['dataset'].str.lower().isin(['nwrd', 'nwrd_wheat_rust', 'nwrd wheat rust'])]
    mask_cov = []
    if not nwrd_df.empty and 'rust_pixel_pct' in nwrd_df.columns:
        cov_vals = nwrd_df['rust_pixel_pct'].dropna()
        if not cov_vals.empty:
            mean_cov = cov_vals.mean()
            mask_cov = [
                f"Found {len(cov_vals)} NWRD images with masks.",
                f"Mean rust coverage: {mean_cov:.2f}%",
                "Proposed patch-labelling rule: Label as RUST if mask coverage > 5.0% else HEALTHY"
            ]
            
    os.makedirs(os.path.join(args.output_dir, 'manifests'), exist_ok=True)
    
    parquet_cols = ['relative_path', 'dataset', 'raw_label', 'canonical_label', 'group_id', 'width', 'height', 'phash', 'dhash', 'phash_variants', 'dhash_variants', 'is_heldout_field_set']
    pq_df = valid_df[parquet_cols].copy()
    pq_df['relative_path'] = pq_df['relative_path'].apply(lambda x: str(Path(x).relative_to(data_root)))
    
    table = pa.Table.from_pandas(pq_df)
    pq.write_table(table, os.path.join(args.output_dir, 'manifests', 'manifest.parquet'))
    
    hist_bins = [0, 2, 4, 6, 8, 10, 12, 14, 16]
    hist_counts, _ = np.histogram(nn_dist, bins=hist_bins + [65])
    hist_dict = {f"{hist_bins[i]}-{hist_bins[i+1]-1}": int(hist_counts[i]) for i in range(len(hist_bins)-1)}
    hist_dict[f">={hist_bins[-1]}"] = int(hist_counts[-1])

    timings['total_time'] = round(time.time() - t_start, 2)
    
    report = {
        'depth_2_tree': tree,
        'image_formats': dict(formats),
        'unreadable_files': unreadable,
        'leakage_analysis': {
            'leaked_test_images_count': int(leaked_test_images),
            'leaked_group_ids': list(map(int, leaked_groups))
        },
        'class_stats': stats_df.to_dict(orient='records'),
        'nwrd_analysis': mask_cov,
        'group_counts_at_thresholds': group_counts,
        'nn_distance_histogram': hist_dict,
        'timings': timings
    }
    
    with open(os.path.join(args.output_dir, 'audit_report.json'), 'w') as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(args.output_dir, 'audit_report.md'), 'w') as f:
        f.write("# Dataset Audit Report\n\n")
        f.write(f"Total Valid Images: {len(valid_df)}\n")
        f.write(f"Unreadable Files: {len(unreadable)}\n\n")
        
        f.write("## Class Statistics\n")
        f.write(stats_df.to_markdown(index=False) + "\n\n")
        
        f.write("## Leakage Analysis\n")
        f.write(f"Leaked Test Images (shared group_id with train): {leaked_test_images}\n\n")
        
        if mask_cov:
            f.write("## NWRD Analysis\n")
            for m in mask_cov:
                f.write(f"- {m}\n")
            f.write("\n")
            
        f.write("## Hash Clustering Analysis\n")
        f.write("### Group Counts at Thresholds\n")
        for t in [2, 4, 6, 8, 10]:
            f.write(f"- Threshold {t}: {group_counts.get(t, 0)} groups\n")
        f.write("\n### NN Distance Histogram\n")
        for k, v in hist_dict.items():
            f.write(f"- {k}: {v}\n")
        f.write("\n")
            
        f.write("## Image Formats\n")
        for k, v in formats.items():
            f.write(f"- {k}: {v}\n")
            
        f.write("\n## Timings\n")
        for k, v in timings.items():
            f.write(f"- {k}: {v}s\n")
            
    generate_contact_sheet(records, os.path.join(args.output_dir, 'contact_sheet.png'))
    generate_cluster_samples(records, near_thresh_pairs, os.path.join(args.output_dir, 'cluster_samples.png'))
    logging.info("Audit complete.")

if __name__ == '__main__':
    main()
