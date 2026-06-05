from flask import Flask, request, jsonify, render_template
from utils import get_sessions, session_count, TRACKS

app = Flask(__name__)


@app.get("/")
def index():
    track = request.args.get("track", "")
    day = request.args.get("day", "")
    speaker = request.args.get("speaker", "")

    sessions = get_sessions(
        track=track or None,
        day=day or None,
        speaker=speaker or None,
    )

    return render_template(
        "index.html",
        sessions=sessions,
        total=session_count(sessions),
        tracks=TRACKS,
        selected_track=track,
        selected_day=day,
        speaker_query=speaker,
    )


@app.get("/api/sessions")
def api_sessions():
    track = request.args.get("track", "")
    day = request.args.get("day", "")
    speaker = request.args.get("speaker", "")

    sessions = get_sessions(
        track=track or None,
        day=day or None,
        speaker=speaker or None,
    )

    return jsonify({
        "sessions": sessions,
        "total": session_count(sessions),
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
