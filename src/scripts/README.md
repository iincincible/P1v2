# 🧠 Tennis Value Betting Scripts

This folder contains all scripts used to build, train, and evaluate the tennis value betting pipeline using Betfair snapshot data and Jeff Sackmann match results.

---

## 📁 Folder Structure

```
scripts/
├── archive/       # Deprecated, superseded, or experimental scripts (safe to ignore)
├── builders/      # Tournament-specific match builders, snapshot joiners, and market scanners
├── debug/         # Tools for inspecting expected value, odds coverage, and match alignment
├── pipeline/      # Core end-to-end pipeline: feature building, training, detection, simulation
├── tools/         # Utility PowerShell scripts for organizing and cleaning the repo
```

---

## 🔁 Typical Pipeline Workflow

1. **Snapshot Parsing** (if needed):
   - `pipeline/parse_betfair_snapshots.py`

2. **Build Clean Match Files**:
   - `builders/build_clean_matches_<tournament>.py`
   - Joins Betfair snapshot-only markets with Sackmann results

3. **Create Odds Features**:
   - `pipeline/build_odds_features.py`

4. **Train Model**:
   - `pipeline/train_win_model_from_odds.py`
   - Or `pipeline/train_eval_model_cross_slam.py` for holdout evaluation

5. **Detect Value Bets**:
   - `pipeline/detect_value_bets.py`

6. **Simulate Bankroll Growth**:
   - `pipeline/simulate_bankroll_growth.py`

---

## 🧪 Debugging Tools

- `debug/debug_ev_distribution.py`: EV & odds distribution inspection
- `debug/debug_check_ltp_matches.py`: LTP coverage check
- `debug/inspect_snapshot_csv.py`: Raw snapshot visual validation

---

## 🛠 Maintenance Utilities

- `tools/archive_deprecated.ps1`: Moves unused scripts to archive
- `tools/reorganize_scripts.ps1`: Automatically reorganizes scripts by role

---

## 🗃 Archived Scripts

You can find older or replaced scripts in:
```
scripts/archive/
```

These include:
- Legacy fuzzy matchers
- Redundant joiners
- Temporary builds

---

## ✅ Status

Your repo is now clean, modular, and ready for scaling or automation.  
Add new tournaments by dropping new builders into `builders/`, and the pipeline will remain stable.
