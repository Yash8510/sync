# Module 03: Spectral Analysis, FFT & Auto-Gain Control (AGC)

## 1. Frequency Analysis Pipeline

The spectral analysis engine ([`ui/main_window.py`](../ui/main_window.py)) computes a real-time Fast Fourier Transform at **$40\text{ FPS}$** ($25.0\text{ ms}$ timer interval) to decompose raw microphone audio into frequency bands for holographic visualizer rendering.

```
 Raw Audio (1024 samples)
            │
            ▼
 Hanning Window Multiplication  w[n] = 0.5 * (1 - cos(2*pi*n / 1023))
            │
            ▼
 Real FFT (rfft) ──> 513 Positive Frequency Bins (0 to 8000 Hz, Δf = 15.625 Hz)
            │
            ▼
 Geometric Log-Bin Partitioning ──> 16 Speech Bands (80 Hz to 4000 Hz)
            │
            ▼
 Dynamic Asymmetric Peak AGC ──> Attack (alpha=0.80) / Decay (alpha=0.05)
            │
            ▼
 Max-Pooling Frequency Bands ──> Bass [0:5], Mid [4:11], Treble [10:16]
```

---

## 2. Windowing & Real FFT Equations

### A. Hanning Windowing (Spectral Leakage Suppression)
To prevent discontinuity artifacts at chunk boundaries, audio samples $x[n]$ for $n \in [0, N-1]$ ($N = 1024$) are modulated by a symmetric Hanning window $w[n]$:

$$w[n] = 0.5 \left( 1 - \cos\left( \frac{2\pi n}{N - 1} \right) \right), \quad n \in \{0, 1, \dots, 1023\}$$
$$\tilde{x}[n] = x[n] \cdot w[n]$$

### B. One-Sided Discrete Fourier Transform (RFFT)
For real-valued signal $\tilde{x}[n]$, the Discrete Fourier Transform yields $K = \frac{N}{2} + 1 = 513$ complex bins:

$$X[k] = \sum_{n=0}^{N-1} \tilde{x}[n] \cdot e^{-j \frac{2\pi k n}{N}}, \quad k \in \{0, 1, \dots, 512\}$$
$$|X[k]| = \sqrt{\text{Re}(X[k])^2 + \text{Im}(X[k])^2}$$

$$\text{Frequency Resolution } \Delta f = \frac{f_s}{N} = \frac{16000}{1024} = 15.625\text{ Hz/bin}$$
$$\text{Bin Center Frequency } f_{\text{center}}(k) = k \cdot 15.625\text{ Hz}$$

---

## 3. Geometric Logarithmic Frequency Binning

Human auditory perception follows a logarithmic frequency scale. The spectrum from $f_{\text{min}} = 80\text{ Hz}$ to $f_{\text{max}} = 4000\text{ Hz}$ (the human vocal fundamental and formant range) is divided into $M = 16$ logarithmically spaced bands:

$$f_i = f_{\text{min}} \cdot \left( \frac{f_{\text{max}}}{f_{\text{min}}} \right)^{\frac{i}{M}} = 80 \cdot (50)^{\frac{i}{16}}, \quad i \in \{0, 1, \dots, 16\}$$
$$\text{Bin Index } k_i = \left\lfloor \frac{f_i \cdot N}{f_s} \right\rfloor = \left\lfloor \frac{f_i \cdot 1024}{16000} \right\rfloor$$

To maintain strict monotonicity when $k_{i+1} \le k_i$, indices are adjusted sequentially:
$$k_{i+1} = \max(k_{i+1}, \, k_i + 1)$$

### Band Energy Integration
The raw energy $E_i$ of band $i$ is the arithmetic mean of bin magnitudes within the interval $[k_i, k_{i+1})$:

$$E_i = \frac{1}{k_{i+1} - k_i} \sum_{k=k_i}^{k_{i+1}-1} |X[k]|, \quad i \in \{0, 1, \dots, 15\}$$

---

## 4. Asymmetric Auto-Gain Control (AGC)

To maintain responsive visualizer animations across whisper-level and loud speech without clipping or latency, the system tracks an adaptive dynamic peak value $\hat{P}_t$:

$$\text{Current Peak } P_t = \max_{i \in [0, 15]} E_{i, t}$$

$$\hat{P}_t = \begin{cases} 
0.20 \cdot \hat{P}_{t-1} + 0.80 \cdot P_t, & \text{if } P_t > \hat{P}_{t-1} \quad (\textbf{Fast Attack: } \tau_{\text{rise}} \approx 30\text{ ms}) \\ 
0.95 \cdot \hat{P}_{t-1} + 0.05 \cdot \max(P_t, 10^{-4}), & \text{if } P_t \le \hat{P}_{t-1} \quad (\textbf{Slow Decay: } \tau_{\text{fall}} \approx 450\text{ ms})
\end{cases}$$

### Normalization
$$\bar{E}_i = \text{clip}\left( \frac{E_i}{\hat{P}_t}, \, 0.0, \, 1.0 \right)$$

---

## 5. Multi-Band Max Pooling

Frequency groups are extracted via max-pooling with a $1.2\times$ saturation factor:

| Band Group | Index Range | Acoustic Focus | Formula |
| :--- | :---: | :--- | :--- |
| **Bass Level** | $i \in [0, 5)$ | Fundamental pitch, plosives ($80\text{--}450\text{ Hz}$) | $L_{\text{bass}} = \min\left(1.2 \cdot \max_{i \in [0, 5)} \bar{E}_i, \, 1.0\right)$ |
| **Mid Level** | $i \in [4, 11)$ | Vowel formants, speech clarity ($350\text{--}1800\text{ Hz}$) | $L_{\text{mid}} = \min\left(1.2 \cdot \max_{i \in [4, 11)} \bar{E}_i, \, 1.0\right)$ |
| **Treble Level** | $i \in [10, 16)$ | Fricatives, sibilance, air ($1500\text{--}4000\text{ Hz}$) | $L_{\text{treble}} = \min\left(1.2 \cdot \max_{i \in [10, 16)} \bar{E}_i, \, 1.0\right)$ |
| **Master Level** | $i \in [0, 16)$ | Overall speech envelope | $L_{\text{master}} = \min\left(1.2 \cdot \max_{i \in [0, 16)} \bar{E}_i, \, 1.0\right)$ |
