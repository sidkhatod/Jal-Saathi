import os
import yaml
from urllib.parse import urlparse
from .schema import Advisory

def get_allowed_domains(advisories_dir):
    path = os.path.join(advisories_dir, 'allowed_domains.txt')
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]

def load_reviewed_advisories(advisories_dir='advisories'):
    reviewed = []
    allowed_domains = get_allowed_domains(advisories_dir)
    
    if not allowed_domains:
        return []
        
    for f in os.listdir(advisories_dir):
        if f.endswith('.yaml'):
            with open(os.path.join(advisories_dir, f), 'r') as file:
                data = yaml.safe_load(file)
                try:
                    adv = Advisory(**data)
                except Exception:
                    continue
                
                if not adv.reviewed:
                    continue
                    
                if not adv.source_org or not adv.source_quote:
                    continue
                    
                if not adv.source_url:
                    continue
                    
                domain = urlparse(adv.source_url).netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                    
                domain_allowed = False
                for ad in allowed_domains:
                    if domain == ad or domain.endswith('.' + ad):
                        domain_allowed = True
                        break
                        
                if not domain_allowed:
                    continue
                    
                reviewed.append(adv)
    return reviewed

def get_advice(crop: str, problem_name: str, advisories_dir: str = None) -> dict:
    if advisories_dir is None:
        advisories_dir = os.path.dirname(__file__)
    loaded = load_reviewed_advisories(advisories_dir)
    for adv in loaded:
        if adv.crop == crop and adv.problem_name == problem_name:
            return adv.model_dump()
            
    return {"status": "no_reviewed_advice", "message_key": "consult_kvk"}
