import os
import yaml
from .schema import Advisory

def load_reviewed_advisories(advisories_dir='advisories'):
    reviewed = []
    for f in os.listdir(advisories_dir):
        if f.endswith('.yaml'):
            with open(os.path.join(advisories_dir, f), 'r') as file:
                data = yaml.safe_load(file)
                adv = Advisory(**data)
                if adv.reviewed:
                    reviewed.append(adv)
    return reviewed
