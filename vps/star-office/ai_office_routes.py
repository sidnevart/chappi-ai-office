"""Flask Blueprint — дополнительные роуты для AI Office (postgres-интеграция).

Подключение в app.py Star Office UI:
    from ai_office_routes import ai_office_bp
    app.register_blueprint(ai_office_bp)
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from flask import Blueprint, jsonify, request

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

ai_office_bp = Blueprint("ai_office", __name__)

STATE_DIR = Path(os.environ.get("CONTROL_STATE_DIR", "/opt/ai-office/openclaw-control/.runtime"))


def _get_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "ai_office"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
    )


def _state_dir():
    return Path(os.environ.get("CONTROL_STATE_DIR", str(STATE_DIR))).resolve()


@ai_office_bp.route("/token-stats")
def token_stats():
    """Статистика токенов из event_log за последние N часов."""
    if not HAS_PSYCOPG2:
        return jsonify({"error": "psycopg2 not installed"}), 503

    hours = int(request.args.get("hours", 24))
    since = datetime.utcnow() - timedelta(hours=hours)

    try:
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                agent_id,
                COUNT(*) AS events,
                COALESCE(SUM(tokens_in), 0)  AS total_tokens_in,
                COALESCE(SUM(tokens_out), 0) AS total_tokens_out,
                COALESCE(SUM(cost_usd), 0)   AS total_cost_usd
            FROM event_log
            WHERE created_at >= %s
            GROUP BY agent_id
            ORDER BY total_cost_usd DESC
            """,
            (since,),
        )
        rows = cur.fetchall()
        conn.close()
        return jsonify({"hours": hours, "stats": [dict(r) for r in rows]})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@ai_office_bp.route("/task-history")
def task_history():
    """Последние задачи из tasks + research_reports."""
    if not HAS_PSYCOPG2:
        return jsonify({"error": "psycopg2 not installed"}), 503

    limit = int(request.args.get("limit", 20))

    try:
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            "SELECT id, title, status, priority, created_at FROM tasks "
            "ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        tasks = [dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT id, query, confidence, created_at FROM research_reports "
            "ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        reports = [dict(r) for r in cur.fetchall()]

        conn.close()
        return jsonify({"tasks": tasks, "research_reports": reports})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@ai_office_bp.route("/log-event", methods=["POST"])
def log_event():
    """Запись события агента в event_log (дополнение к /set_state)."""
    if not HAS_PSYCOPG2:
        return jsonify({"ok": False, "error": "psycopg2 not installed"}), 503

    data = request.get_json(silent=True) or {}
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO event_log
                (agent_id, state, tool_name, model, tokens_in, tokens_out, cost_usd, task_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data.get("agent_id", "main"),
                data.get("state"),
                data.get("tool_name"),
                data.get("model"),
                data.get("tokens_in"),
                data.get("tokens_out"),
                data.get("cost_usd"),
                data.get("task_summary"),
            ),
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@ai_office_bp.route("/agent-state")
def agent_state():
    """Текущее состояние всех агентов из durable job_state и event_log."""
    if not HAS_PSYCOPG2:
        return jsonify({"error": "psycopg2 not installed"}), 503

    try:
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            """
            SELECT agent_id, state, task_summary, tool_name, model, created_at
            FROM event_log
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 100
            """
        )
        recent_events = [dict(r) for r in cur.fetchall()]

        conn.close()

        state_dir = _state_dir()
        jobs = []
        jobs_dir = state_dir / "jobs" / "sdlc"
        if jobs_dir.exists():
            for proj_dir in jobs_dir.iterdir():
                if proj_dir.is_dir():
                    for job_file in proj_dir.glob("*.json"):
                        try:
                            data = json.loads(job_file.read_text(encoding="utf-8"))
                            data["_source"] = str(job_file)
                            jobs.append(data)
                        except Exception:
                            pass

        approvals = []
        approvals_dir = state_dir / "approvals"
        if approvals_dir.exists():
            for app_file in approvals_dir.glob("*.json"):
                try:
                    data = json.loads(app_file.read_text(encoding="utf-8"))
                    data["_source"] = str(app_file)
                    approvals.append(data)
                except Exception:
                    pass

        handoffs = []
        handoffs_dir = state_dir / "handoffs"
        if handoffs_dir.exists():
            for hf_file in handoffs_dir.glob("*.json"):
                try:
                    data = json.loads(hf_file.read_text(encoding="utf-8"))
                    data["_source"] = str(hf_file)
                    handoffs.append(data)
                except Exception:
                    pass

        return jsonify({
            "recent_events": recent_events,
            "jobs": jobs,
            "approvals": approvals,
            "handoffs": handoffs,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@ai_office_bp.route("/artifacts")
def artifacts():
    """Список всех артефактов в durable state."""
    state_dir = _state_dir()
    result = {}
    for subdir in ["jobs", "specs", "approvals", "branches", "prs", "ci", "coder-runs", "events", "outbox", "handoffs"]:
        artifacts = []
        root = state_dir / subdir
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file():
                    try:
                        stat = path.stat()
                        artifacts.append({
                            "path": str(path.relative_to(state_dir)),
                            "size": stat.st_size,
                            "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timedelta(hours=0)).isoformat(),
                        })
                    except Exception:
                        pass
        result[subdir] = artifacts
    return jsonify(result)


@ai_office_bp.route("/thoughts")
def thoughts():
    """Мысли агентов из notes с тегом 'thought'."""
    if not HAS_PSYCOPG2:
        return jsonify({"error": "psycopg2 not installed"}), 503

    agent_id = request.args.get("agent_id")
    limit = int(request.args.get("limit", 50))

    try:
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if agent_id:
            cur.execute(
                """
                SELECT id, content, tags, source, created_at
                FROM notes
                WHERE 'thought' = ANY(tags) AND source = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (agent_id, limit),
            )
        else:
            cur.execute(
                """
                SELECT id, content, tags, source, created_at
                FROM notes
                WHERE 'thought' = ANY(tags)
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify({"thoughts": rows})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
