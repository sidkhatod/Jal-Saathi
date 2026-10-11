import numpy as np
import gymnasium as gym
from gymnasium import spaces
try:
    from rl.utils import load_crop_config, get_forecast
except ImportError:
    from utils import load_crop_config, get_forecast


class PaddyEnv(gym.Env):
    """
    Ponded-water balance environment for Paddy.
    State is ponded depth in mm.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, weather_data, start_day=0, noise_std_rain=1.0, noise_std_et0=0.2):
        super().__init__()
        
        self.weather_data = weather_data
        self.start_day = start_day
        self.noise_std_rain = noise_std_rain
        self.noise_std_et0 = noise_std_et0
        
        # Load Crop Config
        required_keys = [
            'kc_ini', 'kc_mid', 'kc_end', 
            'stage_ini_days', 'stage_dev_days', 'stage_mid_days', 'stage_late_days',
            'percolation_rate', 'bund_height'
        ]
        self.crop_config = load_crop_config('paddy', required_keys)
        
        self.len_ini = self.crop_config['stage_ini_days']
        self.len_dev = self.crop_config['stage_dev_days']
        self.len_mid = self.crop_config['stage_mid_days']
        self.len_late = self.crop_config['stage_late_days']
        self.total_days = self.len_ini + self.len_dev + self.len_mid + self.len_late
        
        self.perc_rate = self.crop_config['percolation_rate']
        self.bund_height = self.crop_config['bund_height']
        
        # Actions: 0: Skip, 1: 20mm, 2: 40mm, 3: 60mm
        self.action_space = spaces.Discrete(4)
        self.action_mapping = [0.0, 20.0, 40.0, 60.0]
        
        # Observation Space
        # [Ponded Depth, Growth Stage Index, Rain_t, ET0_t, Rain_t+1, ET0_t+1, Rain_t+2, ET0_t+2, Days Since Last Irr]
        high = np.array([300.0, 4.0] + [200.0, 20.0]*3 + [365.0], dtype=np.float32)
        low = np.array([-500.0, 0.0] + [0.0, 0.0]*3 + [0.0], dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)
        
        self.reset()

    def _get_kc(self, day_of_season):
        if day_of_season <= self.len_ini:
            return self.crop_config['kc_ini']
        elif day_of_season <= self.len_ini + self.len_dev:
            ratio = (day_of_season - self.len_ini) / self.len_dev
            return self.crop_config['kc_ini'] + ratio * (self.crop_config['kc_mid'] - self.crop_config['kc_ini'])
        elif day_of_season <= self.len_ini + self.len_dev + self.len_mid:
            return self.crop_config['kc_mid']
        else:
            ratio = min(1.0, (day_of_season - (self.len_ini + self.len_dev + self.len_mid)) / self.len_late)
            return self.crop_config['kc_mid'] + ratio * (self.crop_config['kc_end'] - self.crop_config['kc_mid'])

    def _get_stage_index(self, day_of_season):
        if day_of_season <= self.len_ini: return 0.0
        elif day_of_season <= self.len_ini + self.len_dev: return 1.0
        elif day_of_season <= self.len_ini + self.len_dev + self.len_mid: return 2.0
        else: return 3.0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_day = self.start_day
        self.day_of_season = 0
        self.days_since_last_irr = 0.0
        
        # Start with saturated soil / slightly ponded
        self.depth = 10.0 
        
        self.cumulative_stress_days = 0.0
        self.total_irrigation = 0.0
        self.total_overflow = 0.0
        
        return self._get_obs(), {}

    def _get_obs(self):
        stage_idx = self._get_stage_index(self.day_of_season)
        forecast = get_forecast(self.weather_data, self.current_day, self.noise_std_rain, self.noise_std_et0, self.np_random)
        
        obs = np.array([self.depth, stage_idx], dtype=np.float32)
        obs = np.concatenate([obs, forecast, [self.days_since_last_irr]], dtype=np.float32)
        return obs

    def step(self, action):
        irr_mm = self.action_mapping[action]
        if irr_mm > 0:
            self.days_since_last_irr = 0.0
        else:
            self.days_since_last_irr += 1.0
            
        self.total_irrigation += irr_mm
        
        # Weather
        if self.current_day < len(self.weather_data):
            weather = self.weather_data[self.current_day]
            rain = max(0.0, weather.precipitation_sum)
            et0 = max(0.0, weather.et0_fao_evapotranspiration)
        else:
            rain = 0.0
            et0 = 0.0
            
        kc = self._get_kc(self.day_of_season)
        etc = kc * et0
        
        # Balance
        inflow = rain + irr_mm
        # If depth drops below root zone, ETc and perc might stop, but we assume continuous negative drop for simplicity or capped
        outflow = etc + self.perc_rate
        
        self.depth = self.depth + inflow - outflow
        
        overflow = 0.0
        if self.depth > self.bund_height:
            overflow = self.depth - self.bund_height
            self.depth = self.bund_height
            
        self.total_overflow += overflow
            
        stress_day = 0.0
        if self.depth < 0.0:
            stress_day = 1.0
            self.cumulative_stress_days += 1.0
            
        self.current_day += 1
        self.day_of_season += 1
        
        terminated = self.day_of_season >= self.total_days or self.current_day >= len(self.weather_data)
        truncated = False
        
        # Reward: -water penalty - stress penalty only
        reward = -0.01 * irr_mm - stress_day

        info = {
            "depth": self.depth,
            "etc": etc,
            "overflow": overflow,
            "water_applied": irr_mm,
            "stress_days": self.cumulative_stress_days
        }
        
        return self._get_obs(), reward, terminated, truncated, info
