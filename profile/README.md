<div align="center">

<!-- Logo: add profile/assets/logo-light.svg and logo-dark.svg, then uncomment the block below.
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/CandleStack-FEI-STU/.github/main/profile/assets/logo-dark.svg">
  <img alt="CandleStack" src="https://raw.githubusercontent.com/CandleStack-FEI-STU/.github/main/profile/assets/logo-light.svg" height="96">
</picture>
-->

# CandleStack

**Configurable pipeline for pattern analysis in financial time series**

Team project · Faculty of Electrical Engineering and Information Technology, STU in Bratislava · 2026/2027

[Website](https://candlestack.tech) · [Status](https://candlestack.tech/status) · [Meetings](https://candlestack.tech/meetings)

</div>

---

CandleStack is a modular experimentation environment for financial time series.
A user composes an experiment from three interchangeable layers and compares the results:

| Layer | What it does |
| --- | --- |
| **Preprocessing** | Renko, Kagi, time windows, normalization, segmentation |
| **Model** | Runs trained `.keras` models with input and output shape validation |
| **Post-processing** | Thresholds, smoothing, holding period, position sizing and risk limits |

Every run produces an experiment with a unified set of metrics and visualizations.

### Repositories

| Repository | Description |
| --- | --- |
| [candlestack](https://github.com/CandleStack-FEI-STU/candlestack) | Application monorepo |
| [website](https://github.com/CandleStack-FEI-STU/website) | Project website at [candlestack.tech](https://candlestack.tech) |
