import numpy as np
import gymnasium as gym
from gymnasium import spaces
from rl.utils import load_crop_config, get_forecast

class WheatEnv(gym.Env):
    """
    FAO-56 daily root-zone depletion balance environment for Wheat.
    ETc = Kc(stage) * ET0 * Ks
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, weather_data, soil_hydraulics, start_day=0, noise_std_rain=1.0, noise_std_et0=0.2):
        super().__init__()
        
        self.weather_data = weather_data
        self.soil_hydraulics = soil_hydraulics
        self.start_day = start_day
        self.noise_std_rain = noise_std_rain
        self.noise_std_et0 = noise_std_et0
        
        # Load Crop Config
        required_keys = [
            'kc_ini', 'kc_mid', 'kc_end', 
            'max_root_depth_m', 'depletion_fraction',
            'stage_ini_days', 'stage_dev_days', 'stage_mid_days', 'stage_late_days'
        ]
        self.crop_config = load_crop_config('wheat', required_keys)
        
        # Compute stage transitions
        self.len_ini = self.crop_config['stage_ini_days']
        self.len_dev = self.crop_config['stage_dev_days']
        self.len_mid = self.crop_config['stage_mid_days']
        self.len_late = self.crop_config['stage_late_days']
        self.total_days = self.len_ini + self.len_dev + self.len_mid + self.len_late
        
        # Actions: 0: Skip, 1: 20mm, 2: 40mm, 3: 60mm
        self.action_space = spaces.Discrete(4)
        self.action_mapping = [0.0, 20.0, 40.0, 60.0]
        
        # Observation Space
        # [Norm Depletion, Growth Stage Index, Rain_t, ET0_t, Rain_t+1, ET0_t+1, Rain_t+2, ET0_t+2, Days Since Last Irr]
        high = np.array([2.0, 4.0] + [200.0, 20.0]*3 + [365.0], dtype=np.float32)
        low = np.zeros_like(high, dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)
        
        # Yield Ky constants from FAO-33 (Doorenbos and Kassam, 1979)
        # Wheat overall seasonal Ky is ~1.05.
        self.ky = 1.05
        
        self.reset()

    def _get_kc(self, day_of_season):
        if day_of_season <= self.len_ini:
            return self.crop_config['kc_ini']
        elif day_of_season <= self.len_ini + self.len_dev:
            # Interpolate
            ratio = (day_of_season - self.len_ini) / self.len_dev
            return self.crop_config['kc_ini'] + ratio * (self.crop_config['kc_mid'] - self.crop_config['kc_ini'])
        elif day_of_season <= self.len_ini + self.len_dev + self.len_mid:
            return self.crop_config['kc_mid']
        else:
            # Interpolate to end
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
        
        # State: root-zone depletion (Dr) in mm. Starts at field capacity (Dr=0).
        self.dr = 0.0 
        
        # TAW = available water capacity (mm/m) * max_root_depth (m)
        self.taw = self.soil_hydraulics.available_water_capacity_mm_per_m * self.crop_config['max_root_depth_m']
        self.p = self.crop_config['depletion_fraction']
        self.raw = self.p * self.taw
        
        self.cumulative_stress_days = 0.0
        self.total_irrigation = 0.0
        self.sum_eta = 0.0
        self.sum_etc = 0.0
        
        return self._get_obs(), {}

    def _get_obs(self):
        norm_depletion = self.dr / self.taw
        stage_idx = self._get_stage_index(self.day_of_season)
        forecast = get_forecast(self.weather_data, self.current_day, self.noise_std_rain, self.noise_std_et0, self.np_random)
        
        obs = np.array([norm_depletion, stage_idx], dtype=np.float32)
        obs = np.concatenate([obs, forecast, [self.days_since_last_irr]], dtype=np.float32)
        return obs

    def step(self, action):
        irr_mm = self.action_mapping[action]
        if irr_mm > 0:
            self.days_since_last_irr = 0.0
        else:
            self.days_since_last_irr += 1.0
            
        self.total_irrigation += irr_mm
        
        # Current weather
        if self.current_day < len(self.weather_data):
            weather = self.weather_data[self.current_day]
            rain = max(0.0, weather.precipitation_sum)
            et0 = max(0.0, weather.et0_fao_evapotranspiration)
        else:
            rain = 0.0
            et0 = 0.0
            
        # Effective rain rule: 80% of rain is effective, rest runs off or lost
        eff_rain = rain * 0.8
        
        # Calculate ETc and Ks
        kc = self._get_kc(self.day_of_season)
        
        if self.dr < self.raw:
            ks = 1.0
        else:
            ks = max(0.0, min(1.0, (self.taw - self.dr) / (self.taw - self.raw)))
            
        etc = kc * et0
        eta = etc * ks
        
        self.sum_eta += eta
        self.sum_etc += etc
        
        # Water balance update
        # Dr(t) = Dr(t-1) - P_eff - I + ET_a
        self.dr = self.dr - eff_rain - irr_mm + eta
        
        # Deep percolation if Dr < 0
        if self.dr < 0:
            self.dr = 0.0
            
        # Stress tracking
        stress_day = 0.0
        if ks < 1.0:
            stress_day = 1.0
            self.cumulative_stress_days += 1.0
            
        # Advance time
        self.current_day += 1
        self.day_of_season += 1
        
        terminated = self.day_of_season >= self.total_days or self.current_day >= len(self.weather_data)
        truncated = False
        
        # Reward
        # Penalty for water applied (-0.01 per mm)
        reward = -0.01 * irr_mm
        # Penalty for stress (-1 per stress day)
        reward -= stress_day
        
        if terminated:
            # Add yield proxy reward at the end
            # 1 - Ya/Ym = Ky * (1 - ETa/ETc)
            # Ya/Ym = 1 - Ky * (1 - ETa/ETc)
            if self.sum_etc > 0:
                relative_yield = 1.0 - self.ky * (1.0 - (self.sum_eta / self.sum_etc))
            else:
                relative_yield = 0.0
            
            relative_yield = max(0.0, relative_yield)
            reward += relative_yield * 100.0 # Huge bonus for yield

        info = {
            "dr": self.dr,
            "etc": etc,
            "eta": eta,
            "ks": ks,
            "water_applied": irr_mm,
            "stress_days": self.cumulative_stress_days,
            "relative_yield": max(0.0, 1.0 - self.ky * (1.0 - (self.sum_eta / max(1e-6, self.sum_etc))))
        }
        
        return self._get_obs(), reward, terminated, truncated, info
