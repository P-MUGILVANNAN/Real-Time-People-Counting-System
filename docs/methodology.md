# Methodology & Mathematical Formulations

## 1. Problem Formulation
People counting in congested environments presents severe computer vision challenges:
- **Mutual Occlusion**: Overlapping pedestrians occlude body parts, causing standard object detectors to drop detections.
- **Perspective Distortion**: People closer to the camera appear exponentially larger than distant background crowds.
- **Identity Switches**: Heavy occlusion disrupts tracking trajectories, causing duplicate counts.

## 2. Counting Metrics Separation
To ensure research integrity, the system strictly distinguishes:
1. **$N_{det}$ (Frame Detections)**: Total person bounding boxes detected in the current single frame.
2. **$N_{active}$ (Active Tracked)**: Number of unique active tracklets currently being tracked.
3. **$N_{unique}$ (Cumulative Unique)**: Total distinct track IDs observed across the entire session.
4. **$N_{in}, N_{out}, N_{net}$ (Tripwire Line Crossing)**: People crossing a virtual directional tripwire.
5. **$N_{density}$ (Density Regression Integral)**: Continuous crowd count computed by integrating the 2D density surface.
6. **$D_{roi}$ (Regional Occupancy Density)**: Ratio of occupants inside a polygonal boundary relative to pixel area.

## 3. Density Regression Architecture (MCNN)
MCNN addresses scale variation through 3 parallel convolutional columns:
- **Column 1 (Large Heads)**: Filters of size $9 \times 9$, $7 \times 7$. Receptive field: large.
- **Column 2 (Medium Heads)**: Filters of size $7 \times 7$, $5 \times 5$. Receptive field: medium.
- **Column 3 (Small Heads)**: Filters of size $5 \times 5$, $3 \times 3$. Receptive field: small.
- **Output Layer**: $1 \times 1$ convolution combining column features into a continuous $1/4$ resolution density map.

**Loss Function**:
$$\mathcal{L}(\Theta) = \frac{1}{2N} \sum_{i=1}^{N} \| D(X_i; \Theta) - D_i^{GT} \|_2^2$$

## 4. Geometric Occlusion Proxy (SOI)
Because physical 3D ground truth visibility requires depth cameras or lidar, an observable geometric proxy is defined:
$$SOI = w_1 \cdot \text{IoMin}_{mean} + w_2 \cdot \text{Ratio}_{cluster} + w_3 \cdot \text{Penalty}_{scale}$$

Where:
- $\text{IoMin}(A, B) = \frac{\text{Area}(A \cap B)}{\min(\text{Area}(A), \text{Area}(B))}$
- $\text{Ratio}_{cluster}$ = Proportion of people with nearest neighbor distance $\le d_{thresh}$.
- $\text{Penalty}_{scale}$ = Inverse normalized bounding box scale factor.

Categorization:
- **Low**: $SOI < 0.20$
- **Moderate**: $0.20 \le SOI < 0.45$
- **High**: $0.45 \le SOI < 0.70$
- **Severe**: $SOI \ge 0.70$

## 5. Adaptive Hybrid Fusion
$$N_{hybrid} = \alpha(SOI) \cdot N_{track} + (1 - \alpha(SOI)) \cdot N_{density}$$
$$\alpha(SOI) = \max\left(0.1, \min\left(0.9, 0.85 - 0.65 \cdot SOI\right)\right)$$
In sparse scenes ($SOI \approx 0$), $\alpha \approx 0.85$, relying primarily on tracking. In severe congestion ($SOI \approx 1.0$), $\alpha \approx 0.20$, relying on continuous density map integration.
