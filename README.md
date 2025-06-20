# 🎾 Tennis Value Betting Pipeline (P1v2)

*A modern, modular, and fully tested pipeline for finding and simulating value bets in ATP and WTA tennis.*

---

## 🚀 Features

* **Clean end-to-end workflow** for tennis value betting research and simulation
* 📊 Betfair Exchange **snapshot odds** parsing and alignment
* 📁 Jeff Sackmann’s **results** integration for ground-truth and modeling
* 🤖 Logistic regression & flexible modeling for value detection
* 🏦 **Bankroll simulation** with Kelly/flat staking, drawdown, and ROI tracking
* 🧩 Modular pipeline: swap, add, or extend any stage easily
* 🧪 **Automated tests** for critical components (see `tests/`)

---

## 📂 Project Structure

```
project_root/
├── configs/                     # YAML configs for pipelines and tournaments
├── src/scripts/analysis/        # Analysis scripts (EV plots, summaries)
├── src/scripts/builders/        # Match-building and orchestration
├── src/scripts/pipeline/        # Core pipeline stages (features, predict, detect, simulate)
├── src/scripts/utils/           # Shared utilities (CLI, logging, config, normalization)
├── tests/                       # Unit & integration tests
├── data/                        # Raw and processed data files
├── parsed/                      # Intermediate parsed outputs
├── models/                      # Saved models and metadata
├── README.md                    # This file
└── requirements.txt             # Python dependencies
```

---

## ▶️ Quickstart

1. **Configure a tournament**
   Edit or add an entry in `configs/tournaments_YYYY.yaml` with appropriate fields (label, year, thresholds, file paths).

2. **Run the full pipeline:**

   ```bash
   python src/scripts/pipeline/run_full_pipeline.py \
     --config configs/pipeline_run.yaml
   ```

3. **Train a model:**

   ```bash
   python src/scripts/modeling/train_ev_filter_model.py \
     --input_files data/your_train.csv \
     --output_model models/ev_filter.joblib \
     --min_ev 0.2
   ```

---

## 🔄 Batch Pipeline Runs

To process **all tournaments** listed in your tournaments YAML in one go, add `--batch`:

```bash
python src/scripts/pipeline/run_full_pipeline.py \
  --config configs/pipeline_run.yaml \
  --batch
```

Dry-run works here too:

```bash
python src/scripts/pipeline/run_full_pipeline.py \
  --config configs/pipeline_run.yaml \
  --batch \
  --dry_run
```

---

## 📊 Model Reproducibility

Each model training saves, alongside the `.joblib` model file, a metadata `.json` containing:

* **Timestamp** & **git commit hash**
* **Model type** and **feature list**
* **EV threshold**, **training-row count**, and a **data preview**

This ensures experiments can be reproduced exactly.

---

## 🧪 Dry-Run Mode

All major scripts accept `--dry_run` and log planned actions **without** writing or overwriting files. Use for safe testing:

```bash
python src/scripts/analysis/analyze_ev_distribution.py \
  --value_bets_glob "output/*_value_bets.csv" \
  --dry_run
```

---

## ✅ Tests

We keep tests in the top-level `tests/` directory. To run:

```bash
pytest -v
```

Add new tests alongside each new utility or script stage.

---

## 📝 Contributing & Advanced Usage

* Scripts are **importable** via `main(args=None)` for unit tests or interactive use.
* Run `python <script>.py --help` for detailed flags.
* To contribute: open an issue or PR on GitHub.

---

## 📞 Questions or Ideas?

Feel free to open an issue or reach out—happy value betting!
