import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def sliding_window_pmf_weighted(data, window_size, pmf_func, stride=1):
    """
    Apply sliding window with PMF-based weighting.
    
    Parameters:
    - data: input array
    - window_size: size of the sliding window
    - pmf_func: probability mass function (discrete distribution)
    - stride: step size for sliding the window
    """
    n = len(data)
    results = []
    positions = []
    
    # Generate weights based on PMF
    # For discrete distributions, we use integer positions
    k = np.arange(window_size)
    weights = pmf_func(k)
    weights = weights / np.sum(weights)  # Normalize weights
    
    # Slide window across data
    for i in range(0, n - window_size + 1, stride):
        window = data[i:i + window_size]
        weighted_value = np.sum(window * weights)
        results.append(weighted_value)
        positions.append(i + window_size // 2)  # Center position
    
    return np.array(positions), np.array(results), weights

# Example usage
np.random.seed(42)

# Generate sample data: noisy sine wave
t = np.linspace(0, 4*np.pi, 200)
clean_signal = np.sin(t)
noise = np.random.normal(0, 0.2, len(t))
noisy_signal = clean_signal + noise

# Define window parameters
window_size = 21
stride = 1

# Define different PMFs (discrete distributions)
def get_pmf_weights(distribution_name, window_size):
    """Generate PMF weights for different discrete distributions"""
    k = np.arange(window_size)
    
    if distribution_name == 'binomial':
        # Binomial: symmetric around center
        n = window_size - 1
        p = 0.5
        weights = stats.binom.pmf(k, n, p)
    
    elif distribution_name == 'poisson':
        # Poisson: skewed, peak at lambda
        lam = window_size / 2
        weights = stats.poisson.pmf(k, lam)
    
    elif distribution_name == 'geometric':
        # Geometric: exponentially decreasing
        p = 0.15
        weights = stats.geom.pmf(k + 1, p)  # k+1 because geom starts at 1
    
    elif distribution_name == 'hypergeometric':
        # Hypergeometric: symmetric, similar to binomial
        M = window_size * 2  # Population size
        n = window_size      # Number of success states
        N = window_size      # Number of draws
        weights = stats.hypergeom.pmf(k, M, n, N)
    
    elif distribution_name == 'custom_symmetric':
        # Custom symmetric PMF (triangular)
        center = window_size // 2
        weights = np.maximum(0, 1 - np.abs(k - center) / center)
    
    elif distribution_name == 'custom_discrete_gaussian':
        # Discrete approximation of Gaussian
        center = window_size // 2
        sigma = window_size / 6
        weights = np.exp(-0.5 * ((k - center) / sigma) ** 2)
    
    return weights / np.sum(weights)

# Create plots
fig, axes = plt.subplots(3, 2, figsize=(14, 12))
axes = axes.ravel()

# Plot original signal
axes[0].plot(t, noisy_signal, 'b-', alpha=0.5, label='Noisy signal')
axes[0].plot(t, clean_signal, 'k--', label='Clean signal')
axes[0].set_title('Original Signal')
axes[0].legend()
axes[0].grid(True)

# Apply different PMF weightings
distributions = ['binomial', 'poisson', 'geometric', 
                'hypergeometric', 'custom_discrete_gaussian']

for idx, dist_name in enumerate(distributions, 1):
    pmf_func = lambda k: get_pmf_weights(dist_name, window_size)[k]
    positions, smoothed, weights = sliding_window_pmf_weighted(
        noisy_signal, window_size, pmf_func, stride
    )
    
    # Convert positions to time values
    t_positions = t[positions.astype(int)]
    
    axes[idx].plot(t, noisy_signal, 'b-', alpha=0.3, label='Noisy')
    axes[idx].plot(t_positions, smoothed, 'r-', linewidth=2, 
                   label=f'{dist_name.replace("_", " ").title()} weighted')
    axes[idx].plot(t, clean_signal, 'k--', alpha=0.5, label='Clean')
    axes[idx].set_title(f'{dist_name.replace("_", " ").title()} PMF Weighted')
    axes[idx].legend()
    axes[idx].grid(True)

plt.tight_layout()
plt.show()

# Plot the different weight distributions
plt.figure(figsize=(12, 8))

for i, dist_name in enumerate(distributions):
    plt.subplot(2, 3, i+1)
    weights = get_pmf_weights(dist_name, window_size)
    positions = np.arange(window_size)
    
    plt.bar(positions, weights, alpha=0.7, color='steelblue', edgecolor='black')
    plt.title(f'{dist_name.replace("_", " ").title()} PMF')
    plt.xlabel('Position in Window')
    plt.ylabel('Weight')
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Example with adaptive PMF based on local statistics
def adaptive_pmf_weighted(data, window_size, base_dist='binomial'):
    """
    Adaptive PMF weighting that adjusts based on local variance
    """
    n = len(data)
    results = []
    adaptive_params = []
    
    for i in range(n - window_size + 1):
        window = data[i:i + window_size]
        
        # Calculate local statistics
        local_var = np.var(window)
        local_mean = np.mean(window)
        
        # Adapt PMF parameters based on variance
        if base_dist == 'binomial':
            # Higher variance -> more spread out weights
            p = np.clip(0.5 - 0.3 * (local_var - 0.04) / 0.04, 0.2, 0.8)
            weights = stats.binom.pmf(np.arange(window_size), window_size-1, p)
        else:  # custom adaptive
            # Adjust concentration based on local variance
            center = window_size // 2
            spread = max(1, min(center, int(center * (1 + 5 * local_var))))
            k = np.arange(window_size)
            weights = np.maximum(0, 1 - np.abs(k - center) / spread)
        
        weights = weights / np.sum(weights)
        weighted_value = np.sum(window * weights)
        results.append(weighted_value)
        adaptive_params.append(local_var)
    
    return np.array(results), np.array(adaptive_params)

# Apply adaptive PMF weighting
adaptive_smooth, variances = adaptive_pmf_weighted(noisy_signal, window_size)

plt.figure(figsize=(12, 6))

plt.subplot(2, 1, 1)
plt.plot(t, noisy_signal, 'b-', alpha=0.3, label='Noisy signal')
plt.plot(t[:len(adaptive_smooth)], adaptive_smooth, 'r-', linewidth=2, 
         label='Adaptive PMF weighted')
plt.plot(t, clean_signal, 'k--', label='Clean signal')
plt.title('Adaptive PMF-based Smoothing')
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(t[:len(variances)], variances, 'g-', linewidth=2)
plt.title('Local Variance (controls PMF adaptation)')
plt.ylabel('Variance')
plt.xlabel('Time')
plt.grid(True)

plt.tight_layout()
plt.show()

# Comparison of smoothing effectiveness
def calculate_mse(original, smoothed, clean):
    """Calculate mean squared error vs clean signal"""
    min_len = min(len(smoothed), len(clean))
    return np.mean((smoothed[:min_len] - clean[:min_len])**2)

# Compare all methods
methods = {
    'Binomial': lambda: get_pmf_weights('binomial', window_size),
    'Poisson': lambda: get_pmf_weights('poisson', window_size),
    'Geometric': lambda: get_pmf_weights('geometric', window_size),
    'Custom Gaussian': lambda: get_pmf_weights('custom_discrete_gaussian', window_size),
}

mse_results = {}
for name, weight_func in methods.items():
    weights = weight_func()
    pmf_func = lambda k: weights[k]
    _, smoothed, _ = sliding_window_pmf_weighted(noisy_signal, window_size, pmf_func)
    mse = calculate_mse(noisy_signal, smoothed, clean_signal[:len(smoothed)])
    mse_results[name] = mse

# Plot MSE comparison
plt.figure(figsize=(10, 6))
names = list(mse_results.keys())
mse_values = list(mse_results.values())

plt.bar(names, mse_values, color='skyblue', edgecolor='navy')
plt.title('Smoothing Effectiveness (Lower MSE is Better)')
plt.ylabel('Mean Squared Error')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()