import os
import sys
import numpy as np
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from envs.paddy import PaddyEnv

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
    weather = [MockWeather(0.0, 5.0) for _ in range(50)]
    env = PaddyEnv(weather, start_day=0, noise_std_rain=0.0, noise_std_et0=0.0)
    
    env.reset()
    depth_old = env.unwrapped.depth
    
    _, _, _, _, info = env.step(0) # Skip irrigation
    
    depth_new = env.unwrapped.depth
    etc = info["etc"]
    perc = env.unwrapped.perc_rate
    
    assert np.isclose(depth_new - depth_old, -(etc + perc))

def test_mass_balance_and_overflow():
    # Heavy rain to trigger overflow
    weather = [MockWeather(200.0, 5.0) for _ in range(5)]
    env = PaddyEnv(weather, start_day=0, noise_std_rain=0.0, noise_std_et0=0.0)
    
    env.reset()
    env.unwrapped.depth = 50.0
    depth_old = env.unwrapped.depth
    
    _, _, _, _, info = env.step(1) # 20mm irr
    
    depth_new = env.unwrapped.depth
    etc = info["etc"]
    perc = env.unwrapped.perc_rate
    overflow = info["overflow"]
    irr = info["water_applied"]
    rain = 200.0
    
    # new = old + inflow - outflow - overflow
    expected_depth = depth_old + rain + irr - etc - perc - overflow
    assert np.isclose(depth_new, expected_depth)
    assert overflow > 0.0
    assert np.isclose(depth_new, env.unwrapped.bund_height)

def test_determinism():
    weather = [MockWeather(5.0, 5.0) for _ in range(10)]
    
    env1 = PaddyEnv(weather, start_day=0, noise_std_rain=1.0, noise_std_et0=0.2)
    obs1, _ = env1.reset(seed=123)
    next_obs1, r1, _, _, _ = env1.step(2)
    
    env2 = PaddyEnv(weather, start_day=0, noise_std_rain=1.0, noise_std_et0=0.2)
    obs2, _ = env2.reset(seed=123)
    next_obs2, r2, _, _, _ = env2.step(2)
    
    assert np.allclose(obs1, obs2)
    assert np.allclose(next_obs1, next_obs2)
    assert r1 == r2
