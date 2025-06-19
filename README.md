# 🎾 Tennis Value Betting Model (P1v2)

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

## 🔥 Project Status

| Feature                               | Status         |
| ------------------------------------- | -------------- |
| ATP Grand Slam modeling               | ✅ Complete     |
| Indian Wells & multi-tournament flows | ✅ Complete     |
| Value bet detection                   | ✅ Complete     |
| Full bankroll simulation framework    | ✅ Complete     |
| YAML config validation & pipeline     | ✅ Complete     |
| Test suite (pytest)                   | ✅ Complete     |
| Miami and WTA support                 | 🟡 In Progress |
| Player stats and Elo integration      | 🟡 Planned     |
| One-command pipeline launcher         | ✅ Ready        |

---

## 📂 Project Structure

| Folder              | Description                                                    |
| ------------------- | -------------------------------------------------------------- |
| `scripts/pipeline/` | Core pipeline: features, training, prediction, value bets, sim |
| `scripts/builders/` | Tournament/build orchestration and snapshot merging            |
| `scripts/debug/`    | Tools for expected value bins, LTP coverage, misalignments     |
| `data/`             | Raw & processed match/csv data                                 |
| `modeling/`         | Trained models, bankroll logs, value bet outputs               |
| `parsed/`           | Snapshots, clean matches, intermediate files                   |
| `tests/`            | Unit & integration tests for utilities and validation          |

---

## 🛠️ Setup & Installation

**On Windows (PowerShell):**

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**On Mac/Linux:**

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ▶️ Running the Pipeline

**To run the full, end-to-end pipeline:**

```
python scripts/pipeline/run_full_pipeline.py --config configs/pipeline_run.yaml
```

* Edit the YAML config files in `configs/` to choose tournaments, models, or output locations.

**To run individual stages:**

```
python scripts/pipeline/build_odds_features.py --help
python scripts/pipeline/train_eval_model.py --help
python scripts/pipeline/detect_value_bets.py --help
python scripts/pipeline/simulate_bankroll_growth.py --help
```

---

## 🧪 Running Tests

**After activating your virtual environment:**

```
pytest
```

* All unit and integration tests live in the `tests/` directory.
* Critical utilities are covered by tests; expand coverage as you build!

---

## 📝 Contributing & Advanced Usage

* Edit YAML config files in `configs/` for tournaments, defaults, or to enable new features.
* See docstrings in each script for advanced options.
* To contribute: open an issue or PR.

---

## 📞 Questions? Ideas?

Open an issue or reach out—happy value betting!
