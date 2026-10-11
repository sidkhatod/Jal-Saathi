import os
import sys
import json
import argparse
import random
import importlib.util
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Adjust path to import from the data module which is at project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.soil_hydraulics import TEXTURE_LOOKUP
from data.weather import DailyForecast

from envs.wheat import WheatEnv
from envs.paddy import PaddyEnv
from baselines import ContinuousFloodingPolicy, AWDPPolicy, FixedIntervalPolicy, WheatThresholdPolicy

def load_weather_from_parquet(district, start_date, end_date):
    """Load historical weather from local parquet file, no network calls."""
    parquet_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', f'weather_{district.lower()}_2010-2023.parquet')
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Weather data not found at {parquet_path}. Run fetch_weather_history.py first.")
        
    df = pd.read_parquet(parquet_path)
    df['date'] = pd.to_datetime(df['date'])
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
    df_filtered = df.loc[mask].copy()
    df_filtered.sort_values('date', inplace=True)
    
    results = []
    for _, row in df_filtered.iterrows():
        results.append(DailyForecast(
            date=row['date'].strftime('%Y-%m-%d'),
            precipitation_sum=float(row['precipitation_sum']),
            precipitation_probability_max=0,
            wind_speed_10m_max=0.0,
            temperature_2m_max=float(row['temperature_2m_max']),
            temperature_2m_min=float(row['temperature_2m_min']),
            et0_fao_evapotranspiration=float(row['et0_fao_evapotranspiration'])
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
    import onnxruntime as ort
    
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
    
    # Parity Assertion
    ort_sess = ort.InferenceSession(save_path)
    sb3_action, _ = model.predict(dummy_input.numpy(), deterministic=True)
    ort_action = ort_sess.run(None, {'obs': dummy_input.numpy()})[0]
    
    # Check if they are exactly identical (discrete action)
    assert np.allclose(sb3_action, ort_action), f"ONNX parity failed! SB3: {sb3_action}, ONNX: {ort_action}"
    print("ONNX export parity check passed!")

def evaluate_policy_single_env(policy, env, num_episodes=1, start_seed=42):
    all_rewards, all_water, all_stress, all_yield = [], [], [], []
    replay = []
    
    for ep in range(num_episodes):
        obs, _ = env.reset(seed=start_seed+ep)
        done = False
        ep_reward = 0
        ep_replay = []
        
        while not done:
            if hasattr(policy, 'predict'):
                from stable_baselines3 import PPO
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
        
    return all_rewards, all_water, all_stress, all_yield, replay

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", choices=["wheat", "paddy"], required=True)
    parser.add_argument("--timesteps", type=int, default=50000)
    parser.add_argument("--smoke", action="store_true", help="Run a quick smoke test")
    args = parser.parse_args()
    
    if not (os.path.exists("/kaggle/working") or "SM_MODEL_DIR" in os.environ or importlib.util.find_spec("google.colab")):
        print("Training runs on Kaggle/AWS only")
        sys.exit(2)
        
    if args.smoke:
        args.timesteps = 20000
        districts = ["Karnal"]
        test_years = [2021]
    else:
        districts = ["Karnal", "Kurukshetra"]
        test_years = [2021, 2022, 2023]
        
    # Train on 2011-2020 (10 years) for Karnal only (for simplicity in this script)
    train_weather = load_weather_from_parquet("Karnal", "2011-01-01", "2020-12-31")
    
    start_day_crop = 319 if args.crop == 'wheat' else 166
    
    train_env = RandomizedEnvWrapper(args.crop, train_weather, start_day_crop)
    
    print(f"Training PPO on {args.crop} for {args.timesteps} timesteps...")
    from stable_baselines3 import PPO
    model = PPO("MlpPolicy", train_env, verbose=0)
    model.learn(total_timesteps=args.timesteps)
    
    # Baselines
    if args.crop == 'wheat':
        policies = {
            "PPO": model,
            "Fixed-Interval": FixedIntervalPolicy(interval_days=10, action_idx=2),
            "Threshold-based": WheatThresholdPolicy(action_idx=2)
        }
    else:
        policies = {
            "PPO": model,
            "Continuous Flooding": ContinuousFloodingPolicy(),
            "AWD": AWDPPolicy(),
            "Fixed-Interval": FixedIntervalPolicy(interval_days=7, action_idx=2)
        }
        
    print(f"\n--- Evaluation over {len(test_years)} held-out years across districts: {districts} ---")
    
    all_results = {p_name: {"water": [], "stress": [], "yield": []} for p_name in policies.keys()}
    replays = {p_name: [] for p_name in policies.keys()}
    
    for district in districts:
        for year in test_years:
            weather = load_weather_from_parquet(district, f"{year}-01-01", f"{year}-12-31")
            soil = TEXTURE_LOOKUP['loam']
            
            if args.crop == 'wheat':
                env = WheatEnv(weather, soil, start_day=start_day_crop)
            else:
                env = PaddyEnv(weather, start_day=start_day_crop)
                
            for p_name, policy in policies.items():
                _, water, stress, yld, replay = evaluate_policy_single_env(policy, env, num_episodes=1, start_seed=year)
                all_results[p_name]["water"].extend(water)
                all_results[p_name]["stress"].extend(stress)
                all_results[p_name]["yield"].extend(yld)
                # Just save the first trajectory of the first year evaluated for the season replay json
                if not replays[p_name]:
                    replays[p_name] = replay[0]

    # Print Table
    print(f"{'Strategy':<20} | {'Water (mm)':<15} | {'Stress Days':<15} | {'Proxy Yield':<15}")
    print("-" * 72)
    for p_name in policies.keys():
        w_mean, w_std = np.mean(all_results[p_name]["water"]), np.std(all_results[p_name]["water"])
        s_mean, s_std = np.mean(all_results[p_name]["stress"]), np.std(all_results[p_name]["stress"])
        
        y_str = "N/A"
        if all_results[p_name]["yield"]:
            y_mean, y_std = np.mean(all_results[p_name]["yield"]), np.std(all_results[p_name]["yield"])
            y_str = f"{y_mean:.2f} ± {y_std:.2f}"
            
        print(f"{p_name:<20} | {w_mean:.0f} ± {w_std:<9.0f} | {s_mean:.1f} ± {s_std:<9.1f} | {y_str:<15}")
            
    # Export Artifacts
    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    
    export_onnx(model, os.path.join(artifacts_dir, f"ppo_{args.crop}.onnx"))
    
    with open(os.path.join(artifacts_dir, f"{args.crop}_season_replay.json"), 'w') as f:
        json.dump(replays, f, indent=2)
        
    print(f"\nExports saved to {artifacts_dir}")

if __name__ == "__main__":
    main()
