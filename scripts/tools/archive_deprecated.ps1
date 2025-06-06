# Create archive folder if it doesn't exist
if (-not (Test-Path -Path "scripts/archive")) {
    New-Item -ItemType Directory -Path "scripts/archive"
}

Write-Host "📦 Archiving deprecated modeling scripts..."
Move-Item scripts/modeling/train_model_basic.py scripts/archive/
Move-Item scripts/modeling/train_win_model.py scripts/archive/
Move-Item scripts/modeling/train_eval_model_cross_slam.py scripts/archive/

Write-Host "📦 Archiving old match extractor scripts..."
Move-Item scripts/builders/extract_indianwells_wta_matches.py scripts/archive/
Move-Item scripts/builders/extract_wimbledon_wta_matches.py scripts/archive/

Write-Host "📦 Archiving legacy market grouping scripts..."
Move-Item scripts/builders/group_atp_markets_by_tournament.py scripts/archive/
Move-Item scripts/builders/group_wta_markets_by_tournament.py scripts/archive/

Write-Host "📦 Archiving snapshot filter variants..."
Move-Item scripts/builders/filter_snapshots_by_match_ids.py scripts/archive/
Move-Item scripts/builders/filter_snapshots_by_players_and_date.py scripts/archive/
Move-Item scripts/builders/filter_snapshots_to_market_ids.py scripts/archive/
Move-Item scripts/builders/filter_match_rows_with_valid_snapshots.py scripts/archive/

Write-Host "📦 Archiving obsolete debug tools..."
Move-Item scripts/debug/debug_ev_distribution.py scripts/archive/
Move-Item scripts/debug/debug_snapshot_and_odds_coverage.py scripts/archive/
Move-Item scripts/debug/debug_match_coverage.py scripts/archive/
Move-Item scripts/debug/debug_snapshot_coverage.py scripts/archive/
Move-Item scripts/debug/debug_unmatched_runner_pairs.py scripts/archive/
Move-Item scripts/debug/debug_check_ltp_matches.py scripts/archive/

Write-Host "✅ All deprecated scripts moved to scripts/archive/"
