# PowerShell Script: clean_large_files_bfg.ps1

# Ensure you're in your project root before running

# Step 1: Expire reflog and aggressively clean up history
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Step 2: Run BFG to remove large French Open files by name pattern
java -jar bfg.jar --delete-files '*frenchopen_2023*.csv'

# Step 3: Expire again after BFG and clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Step 4: Force push the cleaned history
git push --force
