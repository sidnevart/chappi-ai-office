"""Flask Blueprint — дополнительные роуты для AI Office (postgres-интеграция).

Подключение в app.py Star Office UI:
    from ai_office_routes import ai_office_bp
    app.register_blueprint(ai_office_bp)
"""
import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

ai_office_bp = Blueprint("ai_office", __name__)


def _get_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "ai_office"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
    )


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
