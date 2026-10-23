"""Small standard-library API used by the WebGL frontend."""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bloxorz.config import STAGES_DIR
from bloxorz.engine.stage_loader import load_stage
from bloxorz.solvers.astar import AStarSolver
from bloxorz.solvers.bfs import BFSSolver
from bloxorz.solvers.dfs import DFSSolver
from bloxorz.solvers.ucs import UCSSolver
from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.engine.transitions import transition
from bloxorz.domain.rules import is_goal_state

SOLVERS = {
    "bfs": BFSSolver,
    "dfs": DFSSolver,
    "ucs": UCSSolver,
    "astar": AStarSolver,
}

def _stage_payload(stage: object, level: int) -> dict:
    """Serialize stage metadata needed by the WebGL renderer."""
    switches = [
        {"row": row, "col": col, "actions": actions}
        for (row, col), actions in stage.switches.items()
    ]
    return {
        "level": level,
        "grid": stage.grid,
        "start": list(stage.start_pos),
        "goal": list(stage.goal_pos),
        "bridges": [
            [list(cell) for cell in bridge] for bridge in stage.bridges
        ],
        "initial_bridges": list(stage.initial_bridges),
        "switches": switches,
        "teleports": [
            {
                "row": row,
                "col": col,
                "cube_a": list(values[:2]),
                "cube_b": list(values[2:4]),
                "active_cube": values[4],
            }
            for (row, col), values in stage.teleports.items()
        ],
    }

def _state_payload(state: State, stage: object, valid: bool = True) -> dict:
    return {
        "valid": valid,
        "goal": is_goal_state(state, stage),
        "state": {
            "r1": state.r1,
            "c1": state.c1,
            "r2": state.r2,
            "c2": state.c2,
            "bridges": list(state.bridges),
            "active_cube": state.active_cube,
        },
    }


class SolverHandler(BaseHTTPRequestHandler):
    """Serve solver results as the shared JSON contract."""

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        endpoint = urlparse(self.path).path
        if endpoint not in {"/solve", "/stage"}:
            self._send_json(404, {"status": "FAILED", "error": "Use /solve or /stage"})
            return

        try:
            level = int(query.get("level", ["1"])[0])
            stage_path = STAGES_DIR / f"level_{level:02d}_basic.json"
            if not stage_path.exists():
                matches = sorted(STAGES_DIR.glob(f"level_{level:02d}_*.json"))
                stage_path = matches[0] if matches else stage_path
            stage = load_stage(stage_path)
            if endpoint == "/stage":
                self._send_json(200, _stage_payload(stage, level))
                return
            solver_name = query.get("solver", ["bfs"])[0].lower()
            result = SOLVERS[solver_name](stage).solve()
            self._send_json(200, result.to_dict())
        except (KeyError, ValueError, FileNotFoundError) as exc:
            self._send_json(400, {"status": "FAILED", "error": str(exc)})
        except NotImplementedError as exc:
            self._send_json(501, {"status": "FAILED", "error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"status": "FAILED", "error": str(exc)})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/transition":
            self._send_json(404, {"status": "FAILED", "error": "Use /transition"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size))
            level = int(payload.get("level", 1))
            stage_path = STAGES_DIR / f"level_{level:02d}_basic.json"
            if not stage_path.exists():
                matches = sorted(STAGES_DIR.glob(f"level_{level:02d}_*.json"))
                stage_path = matches[0] if matches else stage_path
            stage = load_stage(stage_path)
            raw_state = payload["state"]
            state = State(
                r1=int(raw_state["r1"]),
                c1=int(raw_state["c1"]),
                r2=int(raw_state["r2"]),
                c2=int(raw_state["c2"]),
                bridges=tuple(bool(value) for value in raw_state["bridges"]),
                active_cube=int(raw_state.get("active_cube", -1)),
            )
            action = Action(str(payload["action"]).upper())
            next_state = transition(state, action, stage)
            if next_state is None:
                self._send_json(200, _state_payload(state, stage, False))
            else:
                self._send_json(200, _state_payload(next_state, stage))
        except (KeyError, TypeError, ValueError, FileNotFoundError) as exc:
            self._send_json(400, {"status": "FAILED", "error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    server = ThreadingHTTPServer(("127.0.0.1", port), SolverHandler)
    print(f"Bloxorz solver API listening on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
