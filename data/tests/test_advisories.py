import os
import yaml
import pytest
from advisories.loader import load_reviewed_advisories, get_advice

def test_loader_rules(tmp_path):
    advisories_dir = tmp_path / "advisories"
    advisories_dir.mkdir()
    
    allowed_domains_file = advisories_dir / "allowed_domains.txt"
    allowed_domains_file.write_text("example.com\nvalid.org")
    
    base_advisory = {
        "name": "Test Problem",
        "crop": "test_crop",
        "problem_name": "test_prob",
        "type": "disease",
        "reviewed": True,
        "source_url": "https://example.com/page",
        "source_org": "Example Org",
        "source_quote": "This is a quote.",
        "chemical_option": "Active Ingredient 10% per CIB&RC label for this crop; confirm with your KVK."
    }
    
    # 1. Valid advisory
    valid = base_advisory.copy()
    (advisories_dir / "valid.yaml").write_text(yaml.dump(valid))
    
    # 2. Unreviewed advisory
    unreviewed = base_advisory.copy()
    unreviewed["reviewed"] = False
    (advisories_dir / "unreviewed.yaml").write_text(yaml.dump(unreviewed))
    
    # 3. Missing source_org
    missing_org = base_advisory.copy()
    missing_org["source_org"] = None
    (advisories_dir / "missing_org.yaml").write_text(yaml.dump(missing_org))
    
    # 4. Missing source_quote
    missing_quote = base_advisory.copy()
    missing_quote["source_quote"] = None
    (advisories_dir / "missing_quote.yaml").write_text(yaml.dump(missing_quote))
    
    # 5. Invalid domain
    invalid_domain = base_advisory.copy()
    invalid_domain["source_url"] = "https://baddomain.com/page"
    (advisories_dir / "invalid_domain.yaml").write_text(yaml.dump(invalid_domain))
    
    loaded = load_reviewed_advisories(str(advisories_dir))
    
    assert len(loaded) == 1
    assert loaded[0].name == "Test Problem"

def test_loader_empty_domains(tmp_path):
    advisories_dir = tmp_path / "advisories"
    advisories_dir.mkdir()
    
    allowed_domains_file = advisories_dir / "allowed_domains.txt"
    allowed_domains_file.write_text("")  # Empty file
    
    base_advisory = {
        "name": "Test Problem",
        "crop": "test_crop",
        "problem_name": "test_prob",
        "type": "disease",
        "reviewed": True,
        "source_url": "https://example.com/page",
        "source_org": "Example Org",
        "source_quote": "This is a quote."
    }
    
    (advisories_dir / "valid.yaml").write_text(yaml.dump(base_advisory))
    
    loaded = load_reviewed_advisories(str(advisories_dir))
    assert loaded == []

def test_get_advice_no_reviewed_advice(tmp_path):
    advisories_dir = tmp_path / "advisories"
    advisories_dir.mkdir()
    
    allowed_domains_file = advisories_dir / "allowed_domains.txt"
    allowed_domains_file.write_text("example.com")
    
    result = get_advice("paddy", "blast", str(advisories_dir))
    assert result == {"status": "no_reviewed_advice", "message_key": "consult_kvk"}

def test_get_advice_success(tmp_path):
    advisories_dir = tmp_path / "advisories"
    advisories_dir.mkdir()
    
    allowed_domains_file = advisories_dir / "allowed_domains.txt"
    allowed_domains_file.write_text("example.com")
    
    base_advisory = {
        "name": "Paddy Blast",
        "crop": "paddy",
        "problem_name": "blast",
        "type": "disease",
        "reviewed": True,
        "source_url": "https://example.com/page",
        "source_org": "Example Org",
        "source_quote": "This is a quote."
    }
    
    (advisories_dir / "paddy_blast.yaml").write_text(yaml.dump(base_advisory))
    
    result = get_advice("paddy", "blast", str(advisories_dir))
    assert result.get("name") == "Paddy Blast"

def test_actual_advisories_chemical_suffix():
    advisories_dir = os.path.join(os.path.dirname(__file__), '../advisories')
    loaded = load_reviewed_advisories(advisories_dir)
    
    assert len(loaded) == 2, f"Expected 2 advisories, got {len(loaded)}"
    
    suffix = "per CIB&RC label for this crop; confirm with your KVK"
    for adv in loaded:
        if adv.chemical_option:
            assert suffix in adv.chemical_option, f"Missing suffix in {adv.name}"
