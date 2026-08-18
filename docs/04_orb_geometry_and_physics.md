# Module 04: Holographic Floating Orb Geometry & Particle Physics

## 1. Widget Coordinate Architecture

The [`FloatingOrb`](../ui/widgets.py) is a frameless, transparent, always-on-top PyQt6 widget (`Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool`).

```
                    (0,0) ────────────────────────── (W, 0)
                      │                                 │
                      │          (cx, cy) Center        │
                      │         (100.0, 100.0)          │
                      │                *                │
                      │          Inner: Bass (R=76)     │
                      │          Mid:   Formant (R=80)  │
                      │          Outer: Sibilance (R=84)│
                      │                                 │
                    (0,H) ────────────────────────── (W, H)
```

### Coordinate Scaling & Trig Cache
For a widget of dimension $(W, H)$ with design reference $D_{\text{ref}} = 200\text{ px}$:

$$S = \frac{\min(W, H)}{200.0}, \quad c_x = \frac{W}{2}, \quad c_y = \frac{H}{2}$$

To eliminate real-time transcendental trigonometric evaluations inside the `paintEvent`, a 200-step precomputation cache is constructed at initialization:

$$\theta_k = \frac{2\pi k}{K}, \quad \cos\theta_k, \quad \sin\theta_k \quad \text{for } k \in \{0, 1, \dots, 199\}, \; K = 200$$

---

## 2. Parametric Polar Wave Equations

Each concentric particle ring $i \in \{0, 1, 2\}$ is defined as a modulated closed polar curve:

$$r_i(\theta_k, t) = R_{\text{base}, i} \cdot S + A_i(t) \cdot S \cdot \sin\left( f_i \cdot \theta_k + \phi_i(t) \right)$$
$$x_i(\theta_k, t) = c_x + r_i(\theta_k, t) \cdot \cos\theta_k$$
$$y_i(\theta_k, t) = c_y + r_i(\theta_k, t) \cdot \sin\theta_k$$

### Ring Parameter Matrix

| Ring Index | Focus | Base Radius ($R_{\text{base}}$) | Spatial Frequency ($f_i$) | Temporal Phase Offset ($\phi_i(t)$) | Dynamic Amplitude $A_i(t)$ | Base Alpha |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ring 0 (Inner)** | Bass | $76.0\text{ px}$ | $5$ | $\text{phase}(t)$ | $0.5 + 18.0 \cdot L_{\text{bass}}$ | $255$ |
| **Ring 1 (Middle)** | Mids | $80.0\text{ px}$ | $7$ | $-1.3 \cdot \text{phase}(t)$ | $0.5 + 14.0 \cdot L_{\text{mid}}$ | $204$ |
| **Ring 2 (Outer)** | Treble | $84.0\text{ px}$ | $4$ | $0.8 \cdot \text{phase}(t)$ | $0.5 + 10.0 \cdot L_{\text{treble}}$ | $170$ |

---

## 3. Dynamic Optics & Gradients

### A. Radial Core Glow (Neon Blue Vignette)
Centered at $(c_x, c_y)$ with radius $R_{\text{glow}} = 90.0 \cdot S$:

$$\text{Alpha}_{\text{core}} = \lfloor 60 + 80 \cdot L_{\text{audio}} \rfloor \in [60, 140]$$
$$\text{Alpha}_{\text{outer}} = \lfloor 20 + 35 \cdot L_{\text{audio}} \rfloor \in [20, 55]$$

* $r = 0.0$: `rgba(0, 102, 255, Alpha_core)` (Saturated Neon Blue)
* $r = 0.6$: `rgba(0, 25, 120, Alpha_outer)` (Deep Royal Blue)
* $r = 1.0$: `rgba(0, 0, 0, 0)` (Full Alpha Falloff)

### B. Rotating Conical Gradient (Particle Coloring)
A `QConicalGradient` centered at $(c_x, c_y)$ rotates with the system phase:

$$\theta_{\text{grad}}(t) = \text{degrees}\left(0.40 \cdot \text{phase}(t)\right) \pmod{360^{\circ}}$$

$$\text{Effective Alpha } \alpha_{\text{eff}} = \left\lfloor \alpha_{\text{base}} \cdot (0.70 + 0.30 \cdot L_{\text{group}}) \right\rfloor$$

* Stop `0.00`: `rgba(0, 255, 255, alpha_eff)` — Solid Cyan
* Stop `0.25`: `rgba(0, 150, 255, alpha_eff)` — Electric Blue
* Stop `0.50`: `rgba(100, 30, 255, alpha_eff)` — Indigo Purple
* Stop `0.75`: `rgba(0, 150, 255, alpha_eff)` — Electric Blue
* Stop `1.00`: `rgba(0, 255, 255, alpha_eff)` — Solid Cyan

---

## 4. Snappy Temporal Easing & Phase Integration

To eliminate lag between speech onset and visual response while preserving fluid motion, the system uses a **first-order Infinite Impulse Response (IIR) smoothing filter**:

$$\text{Phase Velocity } \omega_t = 0.03 + 0.06 \cdot L_{\text{audio}, t}$$
$$\text{phase}_t = \left( \text{phase}_{t-1} + \omega_t \right) \pmod{200\pi}$$

### Smoothing Equations (0.60 History / 0.40 Target)
$$L_{\text{current}, t} = 0.60 \cdot L_{\text{current}, t-1} + 0.40 \cdot L_{\text{target}, t}$$
$$B_{i, \text{smooth}, t} = 0.60 \cdot B_{i, \text{smooth}, t-1} + 0.40 \cdot B_{i, \text{raw}, t}, \quad \forall i \in [0, 15]$$

Pen stroke width is dynamically scaled:
$$W_{\text{pen}} = \max(1.0, \, 3.5 \cdot S)$$
