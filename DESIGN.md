# Design System — Rubik's Snake Visualizer

## Colors (OKLCH)
- **Surface**: oklch(0.18 0.008 260) — deep indigo-tinted near-black
- **Surface raised**: oklch(0.22 0.012 260)
- **Text primary**: oklch(0.92 0.008 80) — warm cream
- **Text secondary**: oklch(0.65 0.01 260)
- **Accent warm**: oklch(0.72 0.18 55) — burnt amber (the classic snake color)
- **Accent cool**: oklch(0.65 0.14 250) — slate blue
- **Valid**: oklch(0.70 0.16 155) — eucalyptus green
- **Invalid**: oklch(0.68 0.16 25) — terracotta red
- **Highlight**: oklch(0.85 0.15 85) — golden

## Typography
- **Headings**: JetBrains Mono, weight 700
- **Body**: Inter, weight 400
- **Data/numbers**: JetBrains Mono, weight 500
- Scale: 1.333 (perfect fourth)

## Elevation
- Cards: 1px border oklch(0.28 0.015 260), no shadow
- Hover: border shifts to accent warm at 0.3 opacity
- Focus: 2px ring accent cool

## Motion
- Transitions: 200ms ease-out-quart
- 3D rotation: continuous 0.02rad/frame idle, user-controlled on drag
- State transitions: 400ms with cubic-bezier(0.16, 1, 0.3, 1)
