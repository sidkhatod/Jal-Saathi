import os
import yaml
from crops.schema import CropParameters

def test_crop_parameters_validity():
    crops_dir = os.path.join(os.path.dirname(__file__), '../crops')
    for f in os.listdir(crops_dir):
        if f.endswith('.yaml'):
            with open(os.path.join(crops_dir, f), 'r') as file:
                data = yaml.safe_load(file)
                parsed = CropParameters(**data)
                assert parsed.citation_url is not None
