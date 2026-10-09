import os
import sys
import json
import argparse
import random
import requests
import numpy as np
from datetime import datetime, timedelta

# Adjust path to import from the data module which is at project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.soil_hydraulics import TEXTURE_LOOKUP
from data.weather import DailyForecast

from stable_baselines3 import PPO
from envs.wheat import WheatEnv
from envs.paddy import PaddyEnv
from baselines import ContinuousFloodingPolicy, AWDPPolicy, FixedIntervalPolicy, WheatThresholdPolicy

def fetch_historical_weather(lat, lon, start_date, end_date):
    """Fetch from Open-Meteo archive API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "et0_fao_evapotranspiration"],
        "timezone": "auto"
    }
    
    cache_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', f'weather_archive_{lat}_{lon}_{start_date}_{end_date}.json')
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            data = json.load(f)
    else:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(data, f)
            
    daily = data.get('daily', {})
    results = []
    for i in range(len(daily.get('time', []))):
        results.append(DailyForecast(
            date=daily['time'][i],
            precipitation_sum=daily['precipitation_sum'][i] if daily['precipitation_sum'][i] is not None else 0.0,
            precipitation_probability_max=0,
            wind_speed_10m_max=0.0,
            temperature_2m_max=daily['temperature_2m_max'][i] if daily['temperature_2m_max'][i] is not None else 25.0,
            temperature_2m_min=daily['temperature_2m_min'][i] if daily['temperature_2m_min'][i] is not None else 15.0,
            et0_fao_evapotranspiration=daily['et0_fao_evapotranspiration'][i] if daily['et0_fao_evapotranspiration'][i] is not None else 4.0
        ))
    return results

class RandomizedEnvWrapper:
    def __init__(self, crop, base_weather, base_start_day, soil_textures=["sand", "loam", "clay"]):
        self.crop = crop
        self.base_weather = base_weather
        self.base_start_day = base_start_day
        self.soil_textures = soil_textures
        self._create_env()

    def _create_env(self):
        soil_tex = random.choice(self.soil_textures)
        soil_hydraulics = TEXTURE_LOOKUP[soil_tex]
        start_day_offset = random.randint(-10, 10)
        start_day = max(0, min(len(self.base_weather) - 1, self.base_start_day + start_day_offset))
        
        if self.crop == 'wheat':
            self.env = WheatEnv(self.base_weather, soil_hydraulics, start_day=start_day)
        else:
            self.env = PaddyEnv(self.base_weather, start_day=start_day)

    def reset(self, seed=None, options=None):
        self._create_env()
        return self.env.reset(seed=seed, options=options)

    def step(self, action):
        return self.env.step(action)
        
    @property
    def action_space(self): return self.env.action_space
    @property
    def observation_space(self): return self.env.observation_space
    @property
    def unwrapped(self): return self.env.unwrapped

def export_onnx(model, save_path):
    import torch
    import torch.onnx
    
    class OnnxablePolicy(torch.nn.Module):
        def __init__(self, policy):
            super().__init__()
            self.policy = policy
        def forward(self, obs):
            return self.policy(obs, deterministic=True)[0]
            
    onnx_policy = OnnxablePolicy(model.policy)
    dummy_input = torch.randn(1, *model.observation_space.shape)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.onnx.export(
        onnx_policy, dummy_input, save_path,
        opset_version=11,
        input_names=["obs"],
        output_names=["action"]
    )

def evaluate_policy(name, policy, env, num_episodes=1):
    all_rewards, all_water, all_stress, all_yield = [], [], [], []
    replay = []
    
    for ep in range(num_episodes):
        obs, _ = env.reset(seed=42+ep)
        done = False
        ep_reward = 0
        ep_replay = []
        
        while not done:
            if hasattr(policy, 'predict'):
                if isinstance(policy, PPO):
                    action, _ = policy.predict(obs, deterministic=True)
                else:
                    action = policy.predict(obs, env)
            else:
                action = policy(obs, env)
                
            next_obs, reward, terminated, truncated, info = env.step(int(action))
            
            state_val = float(env.unwrapped.dr) if hasattr(env.unwrapped, 'dr') else float(env.unwrapped.depth)
            ep_replay.append({
                "day": env.unwrapped.day_of_season,
                "state": state_val,
                "action_mm": float(env.unwrapped.action_mapping[int(action)]),
                "water_applied": float(info["water_applied"]),
                "etc": float(info["etc"])
            })
            
            obs = next_obs
            ep_reward += reward
            done = terminated or truncated
            
        all_rewards.append(ep_reward)
        all_water.append(env.unwrapped.total_irrigation)
        all_stress.append(env.unwrapped.cumulative_stress_days)
        if 'relative_yield' in info:
            all_yield.append(info['relative_yield'])
            
        replay.append(ep_replay)
        
    avg_metrics = {
        "reward": np.mean(all_rewards),
        "water_mm": np.mean(all_water),
        "stress_days": np.mean(all_stress)
    }
    if all_yield:
        avg_metrics["proxy_yield"] = np.mean(all_yield)
        
    return avg_metrics, replay

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", choices=["wheat", "paddy"], required=True)
    parser.add_argument("--timesteps", type=int, default=50000)
    args = parser.parse_args()
    
    # Coordinates for a pilot district (e.g. Karnal, Haryana)
    lat, lon = 29.68, 76.99
    
    # Train years: 2020 to 2022
    train_weather = fetch_historical_weather(lat, lon, "2020-01-01", "2022-12-31")
    # Test year: 2023
    test_weather = fetch_historical_weather(lat, lon, "2023-01-01", "2023-12-31")
    
    # Find start day approx for crop. Wheat: ~Nov 15 (day 319). Paddy: ~Jun 15 (day 166).
    start_day_train = 319 if args.crop == 'wheat' else 166
    start_day_test = 319 if args.crop == 'wheat' else 166
    
    # Train Env
    train_env = RandomizedEnvWrapper(args.crop, train_weather, start_day_train)
    
    # Model
    print(f"Training PPO on {args.crop} for {args.timesteps} timesteps...")
    model = PPO("MlpPolicy", train_env, verbose=1)
    model.learn(total_timesteps=args.timesteps)
    
    # Test Env (deterministic start day, fixed soil texture for fair comparison)
    soil = TEXTURE_LOOKUP['loam']
    if args.crop == 'wheat':
        test_env = WheatEnv(test_weather, soil, start_day=start_day_test)
        baselines = {
            "Fixed-Interval": FixedIntervalPolicy(interval_days=10, action_idx=2),
            "Threshold-based": WheatThresholdPolicy(threshold_norm_depletion=0.7, action_idx=2)
        }
    else:
        test_env = PaddyEnv(test_weather, start_day=start_day_test)
        baselines = {
            "Continuous Flooding": ContinuousFloodingPolicy(),
            "AWD": AWDPPolicy(),
            "Fixed-Interval": FixedIntervalPolicy(interval_days=7, action_idx=2)
        }
        
    # Evaluate
    print("\n--- Evaluation on 2023 Held-Out Year ---")
    results = {}
    replays = {}
    
    # PPO
    metrics, ppo_replay = evaluate_policy("PPO", model, test_env)
    results["PPO"] = metrics
    replays["PPO"] = ppo_replay[0]
    
    # Baselines
    for name, policy in baselines.items():
        metrics, bl_replay = evaluate_policy(name, policy, test_env)
        results[name] = metrics
        replays[name] = bl_replay[0]
        
    for name, m in results.items():
        print(f"{name}:")
        for k, v in m.items():
            print(f"  {k}: {v:.2f}")
            
    # Export Artifacts
    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    
    export_onnx(model, os.path.join(artifacts_dir, f"ppo_{args.crop}.onnx"))
    with open(os.path.join(artifacts_dir, f"{args.crop}_season_replay.json"), 'w') as f:
        json.dump(replays, f, indent=2)
        
    print(f"Exports saved to {artifacts_dir}")

if __name__ == "__main__":
    main()
