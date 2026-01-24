#!/bin/bash

# Repository Cleanup Script
# Based on recommendations in REPOSITORY_ORGANIZATION.md
# Created: 2026-01-24

set -e  # Exit on error

REPO_ROOT="/home/pfoytik/bitcoinTools/warnet"
cd "$REPO_ROOT"

echo "=============================================="
echo "Warnet Repository Cleanup Script"
echo "=============================================="
echo ""
echo "This script will organize the repository by:"
echo "1. Creating archive structure"
echo "2. Moving redundant directories"
echo "3. Archiving old documentation"
echo "4. Archiving legacy scripts"
echo ""
echo "IMPORTANT: This is a DRY RUN by default."
echo "Use --execute flag to actually move files."
echo ""

DRY_RUN=true
if [ "$1" == "--execute" ]; then
    DRY_RUN=false
    echo "⚠️  EXECUTE MODE: Files will be moved!"
    echo "Press Ctrl+C within 5 seconds to cancel..."
    sleep 5
else
    echo "ℹ️  DRY RUN MODE: No files will be moved."
    echo "Use './cleanup_repository.sh --execute' to actually move files."
fi

echo ""

# Function to safely move files/directories
safe_move() {
    local source="$1"
    local dest="$2"
    local description="$3"

    if [ ! -e "$source" ]; then
        echo "⏭️  SKIP: $description (source doesn't exist)"
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "📝 DRY RUN: Would move $source → $dest"
    else
        echo "📦 Moving: $source → $dest"
        mkdir -p "$(dirname "$dest")"
        mv "$source" "$dest"
        echo "   ✓ Done"
    fi
}

# Phase 1: Create Archive Structure
echo "=============================================="
echo "Phase 1: Creating Archive Structure"
echo "=============================================="

if [ "$DRY_RUN" = false ]; then
    mkdir -p archive/2025-01-06-scenarios-snapshot/
    mkdir -p archive/legacy-discovery/
    mkdir -p archive/test-results-dec-2025/
    mkdir -p archive/session-notes/
    mkdir -p archive/early-reports/
    mkdir -p archive/legacy-shell-scripts/
    mkdir -p archive/misc/
    echo "✓ Archive directories created"
else
    echo "📝 Would create archive/ directory structure"
fi

echo ""

# Phase 2: Move Redundant Directories
echo "=============================================="
echo "Phase 2: Moving Redundant Directories"
echo "=============================================="

safe_move \
    "scenarios" \
    "archive/2025-01-06-scenarios-snapshot/scenarios" \
    "Duplicate scenarios directory"

safe_move \
    "discovery" \
    "archive/legacy-discovery/discovery" \
    "Legacy discovery infrastructure"

safe_move \
    "warnet-economic-implementation" \
    "archive/misc/warnet-economic-implementation" \
    "Old economic implementation attempt"

# Move old test results
if [ -d "warnetScenarioDiscovery/test_results" ]; then
    for dir in warnetScenarioDiscovery/test_results/continuous_mining_*; do
        if [ -d "$dir" ]; then
            basename=$(basename "$dir")
            safe_move \
                "$dir" \
                "archive/test-results-dec-2025/$basename" \
                "Old test result: $basename"
        fi
    done
fi

echo ""

# Phase 3: Move Old Documentation
echo "=============================================="
echo "Phase 3: Moving Old Documentation"
echo "=============================================="

safe_move \
    "SESSION_SUMMARY_2025-12-28.md" \
    "archive/session-notes/SESSION_SUMMARY_2025-12-28.md" \
    "Session summary Dec 28"

safe_move \
    "SESSION_SUMMARY_2025-12-29_FORK_DEPTH.md" \
    "archive/session-notes/SESSION_SUMMARY_2025-12-29_FORK_DEPTH.md" \
    "Session summary Dec 29"

safe_move \
    "TASK_0.1_VALIDATION_REPORT.md" \
    "archive/early-reports/TASK_0.1_VALIDATION_REPORT.md" \
    "Early validation report"

safe_move \
    "current_summary.txt" \
    "archive/misc/current_summary.txt" \
    "Old summary file"

echo ""

# Phase 4: Archive Legacy Scripts
echo "=============================================="
echo "Phase 4: Archiving Legacy Scripts"
echo "=============================================="

TOOLS_DIR="warnetScenarioDiscovery/tools"

# List of legacy shell scripts to archive
LEGACY_SCRIPTS=(
    "continuous_mining_test.sh"
    "natural_fork_test.sh"
    "demo_sustained_fork.sh"
    "partition_5node_network.sh"
    "reconnect_5node_network.sh"
    "reconnectNet.sh"
    "reconnect_network.sh"
    "sustained_fork_monitor.sh"
    "manualFork.sh"
    "partition_utils.sh"
    "persistent_monitor.sh"
    "quick_status.sh"
    "quick_summary.sh"
    "run_partition_test.sh"
    "run_tier_1_2_tests.sh"
    "enhanced_fork_monitor.sh"
    "monitor_dual_partition.sh"
)

for script in "${LEGACY_SCRIPTS[@]}"; do
    safe_move \
        "$TOOLS_DIR/$script" \
        "archive/legacy-shell-scripts/$script" \
        "Legacy script: $script"
done

# Archive old documentation
safe_move \
    "$TOOLS_DIR/SUSTAINED_FORK_DEMO.md" \
    "archive/legacy-shell-scripts/SUSTAINED_FORK_DEMO.md" \
    "Old demo documentation"

# Archive old Python scripts that have been superseded
safe_move \
    "$TOOLS_DIR/analyze_fork_depth.py" \
    "archive/legacy-shell-scripts/analyze_fork_depth.py" \
    "Old fork depth analyzer"

safe_move \
    "$TOOLS_DIR/analyze_test_run.py" \
    "archive/legacy-shell-scripts/analyze_test_run.py" \
    "Old test analyzer"

safe_move \
    "$TOOLS_DIR/visualize_test.py" \
    "archive/legacy-shell-scripts/visualize_test.py" \
    "Old visualization script"

echo ""

# Phase 5: Archive monitoring scripts
echo "=============================================="
echo "Phase 5: Archiving Old Monitoring Scripts"
echo "=============================================="

MONITORING_DIR="warnetScenarioDiscovery/monitoring"

safe_move \
    "$MONITORING_DIR/analyze_all_scenarios.py" \
    "archive/legacy-shell-scripts/analyze_all_scenarios.py" \
    "Old batch analyzer"

safe_move \
    "$MONITORING_DIR/assess_criticality.py" \
    "archive/legacy-shell-scripts/assess_criticality.py" \
    "Old criticality assessor"

safe_move \
    "$MONITORING_DIR/test_fork_analyzer.py" \
    "archive/legacy-shell-scripts/test_fork_analyzer.py" \
    "Fork analyzer test"

safe_move \
    "$MONITORING_DIR/monitor_30min_test.sh" \
    "archive/legacy-shell-scripts/monitor_30min_test.sh" \
    "30-min test monitor"

echo ""

# Summary
echo "=============================================="
echo "Cleanup Summary"
echo "=============================================="

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "ℹ️  DRY RUN COMPLETE"
    echo ""
    echo "No files were moved. Review the output above to see what would be moved."
    echo "If everything looks correct, run:"
    echo ""
    echo "    ./cleanup_repository.sh --execute"
    echo ""
    echo "to actually move the files."
else
    echo ""
    echo "✅ CLEANUP COMPLETE"
    echo ""
    echo "Files have been reorganized. The archive/ directory contains:"
    echo "  - Duplicate/legacy code"
    echo "  - Old session notes"
    echo "  - Historical test results"
    echo "  - Deprecated scripts"
    echo ""
    echo "Review the REPOSITORY_ORGANIZATION.md file for the updated structure."
    echo ""
    echo "Recommended next steps:"
    echo "1. Review archive/ contents to confirm nothing important was moved"
    echo "2. Update README.md if needed"
    echo "3. Commit changes to git"
    echo "4. After a few weeks, consider compressing or deleting archive/"
fi

echo ""
echo "=============================================="
