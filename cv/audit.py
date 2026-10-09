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

try:
    import torch
    from torchvision import transforms, models
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

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

def process_image(filepath, class_map):
    """Open image, get stats, compute hashes."""
    rel_path = filepath
    dataset = filepath.parts[0] if len(filepath.parts) > 0 else "unknown"
    raw_label = filepath.parent.name
    canonical_label = class_map.get(raw_label, None)
    
    is_heldout = dataset.lower() in ['nwrd', 'nwrd_wheat_rust', 'nwrd wheat rust', 'riceleafbd']
    
    record = {
        'relative_path': str(filepath),
        'dataset': dataset,
        'raw_label': raw_label,
        'canonical_label': canonical_label,
        'group_id': -1,
        'width': -1,
        'height': -1,
        'phash': None,
        'dhashes': [],
        'phashes': [],
        'is_heldout_field_set': is_heldout,
        'valid': False,
        'format': None,
        'rust_pixel_pct': None
    }
    
    try:
        with Image.open(filepath) as img:
            img_format = img.format
            record['format'] = img_format
            img = img.convert('RGB')
            record['width'], record['height'] = img.size
            record['valid'] = True
            
            # Compute hashes for 8 D4 variants
            variants = get_d4_variants(img)
            # Use fixed size for hashing to speed up
            variants_small = [v.resize((256, 256), Image.Resampling.LANCZOS) for v in variants]
            
            record['phashes'] = [imagehash.phash(v).hash.flatten() for v in variants_small]
            record['dhashes'] = [imagehash.dhash(v).hash.flatten() for v in variants_small]
            
            # Use the first variant's phash as the canonical phash for the parquet
            record['phash'] = str(imagehash.phash(variants_small[0]))
            
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
        return
        
    logging.info(f"Computing hash distances for {N} images...")
    
    def pack_hash(h_list):
        return np.packbits(np.array(h_list), axis=-1).view(np.uint64).squeeze(-1)
        
    p_hashes_packed = np.zeros((N, 8), dtype=np.uint64)
    d_hashes_packed = np.zeros((N, 8), dtype=np.uint64)
    
    for i, r in enumerate(valid_records):
        p_hashes_packed[i] = pack_hash(r['phashes'])
        d_hashes_packed[i] = pack_hash(r['dhashes'])

    batch_size = 1000
    
    def popcount64(x):
        x = x - ((x >> 1) & 0x5555555555555555)
        x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
        x = (x + (x >> 4)) & 0x0f0f0f0f0f0f0f0f
        x = x + (x >> 8)
        x = x + (x >> 16)
        x = x + (x >> 32)
        return x & 0x7f

    for i in range(0, N, batch_size):
        end_i = min(i + batch_size, N)
        p_batch = p_hashes_packed[i:end_i] # (B, 8)
        d_batch = d_hashes_packed[i:end_i]
        
        for j in range(i + 1, N):
            p_xor = p_batch ^ p_hashes_packed[j, 0]
            d_xor = d_batch ^ d_hashes_packed[j, 0]
            
            p_dist = popcount64(p_xor).min(axis=-1)
            d_dist = popcount64(d_xor).min(axis=-1)
            
            matches = (p_dist <= hash_threshold) | (d_dist <= hash_threshold)
            for k in np.where(matches)[0]:
                G.add_edge(i + k, j)

    if use_embeddings and TORCH_AVAILABLE:
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_root', type=str, default=os.environ.get('DATA_ROOT', '/kaggle/input'))
    parser.add_argument('--class_map', type=str, default='cv/class_map.yaml')
    parser.add_argument('--output_dir', type=str, default='cv')
    parser.add_argument('--hash_thresh', type=int, default=8)
    parser.add_argument('--use_embed', action='store_true', default=True)
    parser.add_argument('--embed_thresh', type=float, default=0.97)
    args = parser.parse_args()
    
    data_root = Path(args.data_root)
    if not data_root.exists():
        logging.error(f"Data root {data_root} does not exist.")
        return

    class_map = load_class_map(args.class_map)
    
    logging.info("Scanning dataset tree...")
    tree = scan_folder_tree(data_root)
    
    logging.info("Processing images...")
    records = []
    unreadable = []
    formats = Counter()
    size_dist = []
    
    for root, dirs, files in os.walk(data_root):
        for f in files:
            if is_image(f):
                full_path = Path(root) / f
                try:
                    rel_path = full_path.relative_to(data_root)
                except ValueError:
                    rel_path = full_path
                    
                rec = process_image(rel_path, class_map)
                rec['relative_path'] = str(full_path) 
                
                if rec['valid']:
                    formats[rec['format']] += 1
                    size_dist.append((rec['width'], rec['height']))
                else:
                    unreadable.append(str(rel_path))
                records.append(rec)

    logging.info(f"Found {len(records)} images. {len(unreadable)} unreadable.")
    
    process_nwrd_masks(data_root, records)
    
    compute_group_ids(records, args.hash_thresh, args.use_embed, args.embed_thresh)
    
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
    
    parquet_cols = ['relative_path', 'dataset', 'raw_label', 'canonical_label', 'group_id', 'width', 'height', 'phash', 'is_heldout_field_set']
    pq_df = valid_df[parquet_cols].copy()
    pq_df['relative_path'] = pq_df['relative_path'].apply(lambda x: str(Path(x).relative_to(data_root)))
    
    table = pa.Table.from_pandas(pq_df)
    pq.write_table(table, os.path.join(args.output_dir, 'manifests', 'manifest.parquet'))
    
    report = {
        'depth_2_tree': tree,
        'image_formats': dict(formats),
        'unreadable_files': unreadable,
        'leakage_analysis': {
            'leaked_test_images_count': int(leaked_test_images),
            'leaked_group_ids': list(map(int, leaked_groups))
        },
        'class_stats': stats_df.to_dict(orient='records'),
        'nwrd_analysis': mask_cov
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
            
        f.write("## Image Formats\n")
        for k, v in formats.items():
            f.write(f"- {k}: {v}\n")
            
    generate_contact_sheet(records, os.path.join(args.output_dir, 'contact_sheet.png'))
    logging.info("Audit complete.")

if __name__ == '__main__':
    main()
