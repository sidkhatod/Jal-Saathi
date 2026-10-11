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

class RewardCurveCallback:
    """Callback to track episode returns during training and print a summary."""
    def __init__(self):
        self.episode_rewards = []
        self.current_reward = 0.0

    def init_callback(self, model):
        pass

    def on_step(self) -> bool:
        return True

    def __call__(self, _locals, _globals):
        rewards = _locals.get("rewards")
        dones = _locals.get("dones")
        if rewards is not None and len(rewards) > 0:
            self.current_reward += float(rewards[0])
        if dones is not None and len(dones) > 0 and dones[0]:
            self.episode_rewards.append(self.current_reward)
            self.current_reward = 0.0
        return True

    def print_summary(self):
        print("\n=== Training Reward-Curve Summary ===")
        if not self.episode_rewards:
            print("No completed episodes recorded.")
            print("=====================================\n")
            return
        n = len(self.episode_rewards)
        init_k = min(5, n)
        final_k = min(5, n)
        init_mean = np.mean(self.episode_rewards[:init_k])
        final_mean = np.mean(self.episode_rewards[-final_k:])
        min_r = np.min(self.episode_rewards)
        max_r = np.max(self.episode_rewards)
        mean_r = np.mean(self.episode_rewards)
        print(f"Total Episodes Completed: {n}")
        print(f"Initial Reward (first {init_k} ep avg): {init_mean:.2f}")
        print(f"Final Reward   (last {final_k} ep avg):  {final_mean:.2f}")
        print(f"Min: {min_r:.2f} | Max: {max_r:.2f} | Overall Mean: {mean_r:.2f}")
        if n >= 5:
            segments = np.array_split(self.episode_rewards, min(5, n))
            seg_means = " -> ".join([f"{np.mean(s):.1f}" for s in segments])
            print(f"Reward Curve (5 segments): {seg_means}")
        print("=====================================\n")

def export_onnx(model, save_path, rollout_obs=None):
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
    dummy_input = torch.randn(1, *model.observation_space.shape, dtype=torch.float32)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.onnx.export(
        onnx_policy, dummy_input, save_path,
        opset_version=11,
        input_names=["obs"],
        output_names=["action"]
    )
    
    # Parity Assertion across multiple test observations
    ort_sess = ort.InferenceSession(save_path)
    test_inputs = np.random.randn(20, *model.observation_space.shape).astype(np.float32)
    sb3_actions, _ = model.predict(test_inputs, deterministic=True)
    ort_actions = ort_sess.run(None, {'obs': test_inputs})[0]
    
    max_abs_diff = float(np.max(np.abs(np.array(sb3_actions, dtype=np.float32) - np.array(ort_actions, dtype=np.float32))))
    print(f"ONNX parity: max abs diff = {max_abs_diff}")
    assert max_abs_diff <= 1e-4, f"ONNX parity failed! max abs diff = {max_abs_diff} > 1e-4"

    # Save 5 (observation, ONNX action) pairs to rl/artifacts/golden_obs.json
    rl_artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
    os.makedirs(rl_artifacts_dir, exist_ok=True)
    
    sample_obs = rollout_obs[:5] if (rollout_obs is not None and len(rollout_obs) >= 5) else [test_inputs[i] for i in range(5)]
    golden_pairs = []
    for obs in sample_obs:
        obs_np = np.array(obs, dtype=np.float32).reshape(1, -1)
        onnx_act = int(ort_sess.run(None, {'obs': obs_np})[0][0])
        golden_pairs.append({
            "observation": [round(float(x), 4) for x in obs],
            "onnx_action": onnx_act
        })
    with open(os.path.join(rl_artifacts_dir, 'golden_obs.json'), 'w') as f:
        json.dump(golden_pairs, f, indent=2)
    print(f"Saved 5 golden observation-action pairs to {os.path.join(rl_artifacts_dir, 'golden_obs.json')}")

def evaluate_policy_single_env(policy, env, num_episodes=1, start_seed=42):
    all_rewards, all_water, all_stress = [], [], []
    replay = []
    collected_obs = []
    is_wheat = hasattr(env.unwrapped, 'dr')
    
    for ep in range(num_episodes):
        obs, _ = env.reset(seed=start_seed+ep)
        done = False
        ep_reward = 0
        ep_replay = []
        
        while not done:
            collected_obs.append(obs.copy())
            if hasattr(policy, 'predict'):
                from stable_baselines3 import PPO
                if isinstance(policy, PPO):
                    action, _ = policy.predict(obs, deterministic=True)
                else:
                    action = policy.predict(obs, env)
            else:
                action = policy(obs, env)
                
            next_obs, reward, terminated, truncated, info = env.step(int(action))
            
            day_record = {
                "day": int(env.unwrapped.day_of_season),
                "action_mm": float(env.unwrapped.action_mapping[int(action)]),
                "water_applied": float(info["water_applied"]),
                "etc": float(info["etc"])
            }
            if is_wheat:
                day_record["depletion_mm"] = float(env.unwrapped.dr)
            else:
                day_record["ponded_mm"] = float(env.unwrapped.depth)
                
            ep_replay.append(day_record)
            
            obs = next_obs
            ep_reward += reward
            done = terminated or truncated
            
        all_rewards.append(ep_reward)
        all_water.append(env.unwrapped.total_irrigation)
        all_stress.append(env.unwrapped.cumulative_stress_days)
        replay.append(ep_replay)
        
    return all_rewards, all_water, all_stress, replay, collected_obs

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
    reward_callback = RewardCurveCallback()
    model.learn(total_timesteps=args.timesteps, callback=reward_callback)
    
    # Print Reward Curve Summary
    reward_callback.print_summary()
    
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
    
    all_results = {p_name: {"water": [], "stress": []} for p_name in policies.keys()}
    replays = {p_name: [] for p_name in policies.keys()}
    ppo_rollout_obs = []
    
    for district in districts:
        for year in test_years:
            weather = load_weather_from_parquet(district, f"{year}-01-01", f"{year}-12-31")
            soil = TEXTURE_LOOKUP['loam']
            
            if args.crop == 'wheat':
                env = WheatEnv(weather, soil, start_day=start_day_crop)
            else:
                env = PaddyEnv(weather, start_day=start_day_crop)
                
            for p_name, policy in policies.items():
                _, water, stress, replay, obs_list = evaluate_policy_single_env(policy, env, num_episodes=1, start_seed=year)
                all_results[p_name]["water"].extend(water)
                all_results[p_name]["stress"].extend(stress)
                if p_name == "PPO" and not ppo_rollout_obs:
                    ppo_rollout_obs = obs_list
                # Save the first trajectory of the first held-out season for the replay json
                if not replays[p_name]:
                    replays[p_name] = replay[0]

    # Print Evaluation Table
    print(f"{'Strategy':<20} | {'Water (mm)':<15} | {'Stress Days':<15}")
    print("-" * 56)
    for p_name in policies.keys():
        w_mean, w_std = np.mean(all_results[p_name]["water"]), np.std(all_results[p_name]["water"])
        s_mean, s_std = np.mean(all_results[p_name]["stress"]), np.std(all_results[p_name]["stress"])
        print(f"{p_name:<20} | {w_mean:.0f} ± {w_std:<9.0f} | {s_mean:.1f} ± {s_std:<9.1f}")
            
    # Export Artifacts
    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    
    export_onnx(model, os.path.join(artifacts_dir, f"ppo_{args.crop}.onnx"), rollout_obs=ppo_rollout_obs)
    
    # Save season replay JSON matching schema in docs/CONTRACTS.md
    with open(os.path.join(artifacts_dir, f"{args.crop}_season_replay.json"), 'w') as f:
        json.dump(replays["PPO"], f, indent=2)
    with open(os.path.join(artifacts_dir, "season_replay.json"), 'w') as f:
        json.dump(replays["PPO"], f, indent=2)
        
    print(f"\nExports saved to {artifacts_dir}")

if __name__ == "__main__":
    main()

