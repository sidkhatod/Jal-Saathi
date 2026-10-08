import os
import pytest
from advisories.loader import load_reviewed_advisories

def test_loader_filters_unreviewed():
    advisories_dir = os.path.join(os.path.dirname(__file__), '../advisories')
    reviewed = load_reviewed_advisories(advisories_dir)
    assert len(reviewed) == 2
