import os
import sys
import numpy as np
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from envs.wheat import WheatEnv

# Mock soil hydraulics and weather
class MockSoil:
    def __init__(self):
        self.available_water_capacity_mm_per_m = 100.0

class MockWeather:
    def __init__(self, rain, et0):
        self.precipitation_sum = rain
        self.et0_fao_evapotranspiration = et0

@pytest.fixture(autouse=True)
def set_env():
    os.environ["USE_FAKE_CONFIG"] = "1"
    yield
    del os.environ["USE_FAKE_CONFIG"]

def test_no_rain_no_irrigation():
    # Rain=0, ET0=5
    weather = [MockWeather(0.0, 5.0) for _ in range(50)]
    soil = MockSoil()
    env = WheatEnv(weather, soil, start_day=0, noise_std_rain=0.0, noise_std_et0=0.0)
    
    obs, _ = env.reset()
    dr_old = env.unwrapped.dr
    
    _, _, _, _, info = env.step(0) # Skip irrigation
    
    # Dr should increase by exactly ETc (since Ks is 1 initially and no rain/irr)
    dr_new = env.unwrapped.dr
    etc = info["etc"]
    
    assert np.isclose(dr_new - dr_old, etc)

def test_mass_balance():
    # Rain=10, ET0=5
    weather = [MockWeather(10.0, 5.0) for _ in range(50)]
    soil = MockSoil()
    env = WheatEnv(weather, soil, start_day=0, noise_std_rain=0.0, noise_std_et0=0.0)
    
    env.reset()
    # Artificially set Dr so it doesn't hit 0 bounds
    env.unwrapped.dr = 20.0
    dr_old = env.unwrapped.dr
    
    _, _, _, _, info = env.step(1) # 20mm irr
    
    dr_new = env.unwrapped.dr
    eta = info["eta"]
    irr = info["water_applied"]
    eff_rain = 10.0 * 0.8
    
    # Balance equation: Dr_new = Dr_old - eff_rain - irr + eta
    expected_dr = max(0.0, dr_old - eff_rain - irr + eta)
    assert np.isclose(dr_new, expected_dr)

def test_ks_bounds():
    weather = [MockWeather(0.0, 10.0) for _ in range(100)] # High ET0
    soil = MockSoil()
    env = WheatEnv(weather, soil, start_day=0)
    
    env.reset()
    env.unwrapped.dr = 99.0 # Almost all depleted (TAW = 100)
    
    _, _, _, _, info = env.step(0)
    ks = info["ks"]
    
    assert 0.0 <= ks <= 1.0

def test_determinism():
    weather = [MockWeather(5.0, 5.0) for _ in range(10)]
    soil = MockSoil()
    
    env1 = WheatEnv(weather, soil, start_day=0, noise_std_rain=1.0, noise_std_et0=0.2)
    obs1, _ = env1.reset(seed=42)
    next_obs1, r1, _, _, _ = env1.step(1)
    
    env2 = WheatEnv(weather, soil, start_day=0, noise_std_rain=1.0, noise_std_et0=0.2)
    obs2, _ = env2.reset(seed=42)
    next_obs2, r2, _, _, _ = env2.step(1)
    
    assert np.allclose(obs1, obs2)
    assert np.allclose(next_obs1, next_obs2)
    assert r1 == r2
