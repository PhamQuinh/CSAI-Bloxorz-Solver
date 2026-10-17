"""Automated benchmark runner: evaluates all 4 solvers across all 10 stages.
Managed by TV5 - QA & Report.
"""
from bloxorz.config import STAGES_DIR, RESULTS_DIR
from bloxorz.engine.stage_loader import load_stage
from bloxorz.solvers.bfs import BFSSolver

def run_benchmark():
    print("Starting Bloxorz Benchmark Suite...")
    # TODO (TV5): Loop through stages and run BFS, DFS, UCS, A*
    pass

if __name__ == "__main__":
    run_benchmark()
