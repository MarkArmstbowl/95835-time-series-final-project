# Interface prototype

The current [PeakPlan Figma prototype](https://pleat-star-72791443.figma.site/) shows the monthly outlook, forecast-accuracy view, a what-if calculation, and forecast-related questions. Its forecast and accuracy numbers are currently samples.

Store interface exports, screenshots selected for the submission, and user-flow diagrams in this folder. Future application source code belongs in `app/`.

The interface and model outputs should use the same geographic segment, data cutoff, dates, and units. Replace sample numbers and explanations with the final forecasts and evaluation results when available.

For integration previews, pick one model and training window for each region and metric from [candidate_forecasts.csv](../outputs/forecasts/candidate_forecasts.csv). After evaluation, use `outputs/forecasts/final_forecasts.csv` for the outlook and `outputs/evaluation/app_accuracy.csv` for the accuracy view. Display occupancy fractions as percentages, ADR as USD, and absolute occupancy errors in percentage points. The [Part 3 handoff](../docs/modeling_handoff.md) describes the planned export fields and available context for the calendar and what-if page.
