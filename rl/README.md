# Jal-Saathi RL Environments

This module contains two `gymnasium` environments for learning irrigation policies using `stable-baselines3` (PPO). The training pipeline is offline and optimized for Kaggle CPU environments.

## Modelling Assumptions

### 1. Dynamics & Effective Rain
- **WheatEnv** (FAO-56 Root-Zone Depletion): 
  - Effective Rain ($P_{eff}$) is modelled simply as $0.8 \times \text{Rain}$. 
  - Excess rain is routed to deep percolation ($D_r \ge 0$).
  - $ET_c$ is calculated dynamically using stage-based $K_c$ and standard FAO-56 depletion formulas to yield $K_s$.
- **PaddyEnv** (Ponded-Water Balance):
  - Rain contributes $100\%$ to the ponded depth until the water level hits `bund_height`, after which it overflows.
  - Constant rate percolation acts as an outflow alongside $ET_c$.

### 2. Weather & Forecast Noise
- The environments use actual multi-year historical weather fetched via Open-Meteo.
- A 3-day forecast is presented in the observation space. The forecast adds Gaussian noise to the true upcoming weather.
- Default noise parameters: $\sigma_{\text{Rain}} = 1.0$ mm, $\sigma_{ET_0} = 0.2$ mm.

### 3. Reward Formulation
The daily reward is calculated strictly as:
- **Water Penalty**: $-0.01$ per mm of water applied.
- **Stress Penalty**: $-1.0$ per stress day.
- **Reward**: `Reward = -water penalty - stress penalty` only (no terminal yield bonus).

### 4. Yield Proxy ($K_y$)
- **Not used**: $K_y$ has been removed entirely (the previously cited "FAO-33 Table 24, 1.05" cannot be independently verified). Both WheatEnv and PaddyEnv evaluate and penalize water stress directly via cumulative stress days rather than an unverified empirical yield multiplier.

### 5. Initial Conditions
- **WheatEnv**: Starts at field capacity, meaning root-zone depletion $D_r = 0.0$ mm.
- **PaddyEnv**: Starts slightly flooded at $10.0$ mm ponded depth.
- In both cases, the `days_since_last_irr` counter starts at 0.

### 6. Randomisation
During training in `RandomizedEnvWrapper`, each episode randomly shifts environmental constraints to improve generalization:
- **Soil Texture**: Sampled uniformly from `["sand", "loam", "clay"]`, pulling hydraulic limits from `data/soil_hydraulics.py`.
- **Sowing Date**: Offset by a uniformly sampled value of $\pm 10$ days around the base sowing date.