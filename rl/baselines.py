import numpy as np

class ContinuousFloodingPolicy:
    def __init__(self, target_depth=50.0):
        self.target_depth = target_depth

    def predict(self, obs, env):
        # env state gives us the actual depth without noise
        depth = env.unwrapped.depth
        if depth < self.target_depth:
            deficit = self.target_depth - depth
            if deficit >= 60: return 3
            elif deficit >= 40: return 2
            elif deficit >= 20: return 1
            else: return 0
        return 0

class AWDPPolicy:
    def __init__(self, lower_threshold=-150.0, target_depth=50.0):
        self.lower_threshold = lower_threshold
        self.target_depth = target_depth

    def predict(self, obs, env):
        depth = env.unwrapped.depth
        if depth <= self.lower_threshold:
            deficit = self.target_depth - depth
            if deficit >= 60: return 3
            elif deficit >= 40: return 2
            elif deficit >= 20: return 1
            else: return 1 # At least 20mm
        return 0

class FixedIntervalPolicy:
    def __init__(self, interval_days=7, action_idx=2): # e.g. 40mm every 7 days
        self.interval_days = interval_days
        self.action_idx = action_idx

    def predict(self, obs, env):
        days_since = obs[-1] # Days since last irr
        if days_since >= self.interval_days:
            return self.action_idx
        return 0

class WheatThresholdPolicy:
    def __init__(self, action_idx=2): # e.g. 2 = 40mm
        self.action_idx = action_idx

    def predict(self, obs, env):
        depletion = env.unwrapped.dr
        raw = env.unwrapped.raw
        if depletion >= raw:
            return self.action_idx
        return 0
