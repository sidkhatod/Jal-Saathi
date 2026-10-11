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
The daily reward is calculated as:
- **Water Penalty**: $-0.01$ per mm of water applied.
- **Stress Penalty**: $-1.0$ per stress day.
- **Terminal Yield Proxy**: 
  - **Wheat**: $+100 \times \text{Relative Yield}$
  - **Paddy**: $-50 \times (\text{Stress Days} / \text{Total Days})$

### 4. Yield Proxy ($K_y$)
- **Wheat**: Uses the FAO-33 empirical yield response factor formula: $1 - Y_a/Y_m = K_y (1 - ET_a / ET_c)$. The seasonal $K_y$ for wheat is fixed at $1.05$. 
  - **Source**: FAO-33 (Doorenbos and Kassam, 1979), *Table 24. Yield Response Factor (Ky)*, Row: "Winter Wheat".
- **Paddy**: *Not used.* Since robust stage-specific $K_y$ values for paddy ponding are highly variable and context-dependent, PaddyEnv falls back strictly to penalizing cumulative stress days instead.

### 5. Initial Conditions
- **WheatEnv**: Starts at field capacity, meaning root-zone depletion $D_r = 0.0$ mm.
- **PaddyEnv**: Starts slightly flooded at $10.0$ mm ponded depth.
- In both cases, the `days_since_last_irr` counter starts at 0.

### 6. Randomisation
During training in `RandomizedEnvWrapper`, each episode randomly shifts environmental constraints to improve generalization:
- **Soil Texture**: Sampled uniformly from `["sand", "loam", "clay"]`, pulling hydraulic limits from `data/soil_hydraulics.py`.
- **Sowing Date**: Offset by a uniformly sampled value of $\pm 10$ days around the base sowing date.