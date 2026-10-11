import os
import sys
import shutil
import tempfile
import pytest
from PIL import Image, ImageDraw, ImageEnhance
import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import audit

def create_random_image(path, seed):
    np.random.seed(seed)
    img = Image.new('RGB', (100, 100), color=(
        int(np.random.randint(0, 50)),
        int(np.random.randint(0, 50)),
        int(np.random.randint(0, 50))
    ))
    draw = ImageDraw.Draw(img)
    
    x0, y0 = np.random.randint(10, 40, 2)
    x1, y1 = np.random.randint(60, 90, 2)
    draw.rectangle([x0, y0, x1, y1], fill=(
        int(np.random.randint(100, 255)),
        int(np.random.randint(100, 255)),
        int(np.random.randint(100, 255))
    ))
    
    ex0, ey0 = np.random.randint(0, 50, 2)
    ex1, ey1 = np.random.randint(50, 100, 2)
    draw.ellipse([ex0, ey0, ex1, ey1], fill=(
        int(np.random.randint(100, 255)),
        int(np.random.randint(100, 255)),
        int(np.random.randint(100, 255))
    ))
    
    img.save(path)
    return img

@pytest.fixture
def synthetic_data_env():
    temp_dir = tempfile.mkdtemp()
    
    dataset1 = os.path.join(temp_dir, 'dataset1')
    dataset2 = os.path.join(temp_dir, 'nwrd') 
    
    os.makedirs(os.path.join(dataset1, 'class_a'))
    os.makedirs(os.path.join(dataset1, 'class_b'))
    os.makedirs(os.path.join(dataset2, 'class_a'))
    os.makedirs(os.path.join(dataset2, 'masks'))
    
    images = []
    for i in range(6):
        img_path = os.path.join(dataset1, 'class_a', f'img_a_{i}.png')
        img = create_random_image(img_path, seed=i)
        images.append((img, img_path))
        
        img_path = os.path.join(dataset1, 'class_b', f'img_b_{i}.png')
        img = create_random_image(img_path, seed=i+10)
        images.append((img, img_path))
        
    img1 = images[0][0]
    img1_flip = img1.transpose(Image.FLIP_LEFT_RIGHT)
    img1_flip.save(os.path.join(dataset2, 'class_a', 'img_a_0_flip.png'))
    
    mask_arr = np.zeros((100, 100), dtype=np.uint8)
    mask_arr[40:60, 40:60] = 255
    mask_img = Image.fromarray(mask_arr)
    mask_img.save(os.path.join(dataset2, 'masks', 'img_a_0_flip.png'))
    
    img2 = images[2][0]
    img2_rot = img2.rotate(90, expand=True)
    img2_rot.save(os.path.join(dataset2, 'class_a', 'img_a_1_rot.png'))
    
    img3 = images[4][0]
    enhancer = ImageEnhance.Brightness(img3)
    img3_bright = enhancer.enhance(1.5)
    img3_bright.save(os.path.join(dataset2, 'class_a', 'img_a_2_bright.png'))
    
    yield temp_dir
    
    # Don't delete so we can debug if needed
    # shutil.rmtree(temp_dir)

def test_audit_pipeline(synthetic_data_env):
    data_root = synthetic_data_env
    output_dir = os.path.join(data_root, 'output')
    
    class_map_path = os.path.join(data_root, 'class_map.yaml')
    with open(class_map_path, 'w') as f:
        f.write("folder_mapping:\n  class_a: class_a_canon\n  class_b: class_b_canon\n")
        
    sys.argv = ['audit.py', '--data_root', data_root, '--class_map', class_map_path, '--output_dir', output_dir, '--hash_thresh', '8']
    audit.main()
    
    import json
    report_path = os.path.join(output_dir, 'audit_report.json')
    assert os.path.exists(report_path)
    
    with open(report_path, 'r') as f:
        report = json.load(f)
        
    manifest_path = os.path.join(output_dir, 'manifests', 'manifest.parquet')
    assert os.path.exists(manifest_path)
    
    table = pq.read_table(manifest_path)
    df = table.to_pandas()
    
    print("\n--- Manifest DataFrame ---")
    print(df[['relative_path', 'group_id', 'is_heldout_field_set']])
    print("--- Report ---")
    print(json.dumps(report, indent=2))
    
    # Check groupings
    id1 = df[df['relative_path'].str.contains('img_a_0.png')]['group_id'].values[0]
    id1_flip = df[df['relative_path'].str.contains('img_a_0_flip.png')]['group_id'].values[0]
    assert id1 == id1_flip, f"Flip match failed: {id1} vs {id1_flip}"
    
    id2 = df[df['relative_path'].str.contains('img_a_1.png')]['group_id'].values[0]
    id2_rot = df[df['relative_path'].str.contains('img_a_1_rot.png')]['group_id'].values[0]
    assert id2 == id2_rot, f"Rotate match failed: {id2} vs {id2_rot}"
    
    id3 = df[df['relative_path'].str.contains('img_a_2.png')]['group_id'].values[0]
    id3_bright = df[df['relative_path'].str.contains('img_a_2_bright.png')]['group_id'].values[0]
    assert id3 == id3_bright, f"Brightness match failed: {id3} vs {id3_bright}"
    
    assert id1 != id2 and id1 != id3 and id2 != id3, f"Base images matched each other! {id1}, {id2}, {id3}"
    
    unique_groups = df['group_id'].nunique()
    assert unique_groups == 12, f"Expected 12 unique groups, found {unique_groups}"
    
    assert report['leakage_analysis']['leaked_test_images_count'] == 3
    
    assert len(report['nwrd_analysis']) > 0
    assert '4.00%' in report['nwrd_analysis'][1]
