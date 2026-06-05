TRACKS = ["AI & ML", "Cloud", "Mobile", "Web", "Security"]

SESSIONS = [
    {"id": 1,  "title": "Building Agents with Gemini",       "speaker": "Abi Aryan",          "track": "AI & ML", "day": 1, "time": "09:00", "room": "Hall A", "level": "Beginner"},
    {"id": 2,  "title": "Cloud Run at Scale",                "speaker": "David Goulding",      "track": "Cloud",   "day": 1, "time": "10:00", "room": "Hall B", "level": "Intermediate"},
    {"id": 3,  "title": "Flutter 4.0 Deep Dive",             "speaker": "Mariam Hassan",       "track": "Mobile",  "day": 1, "time": "11:00", "room": "Hall C", "level": "Advanced"},
    {"id": 4,  "title": "Vertex AI in Production",           "speaker": "Eric Schmidt",        "track": "AI & ML", "day": 1, "time": "14:00", "room": "Hall A", "level": "Intermediate"},
    {"id": 5,  "title": "Firebase: What's New",              "speaker": "Sara Robinson",       "track": "Cloud",   "day": 1, "time": "15:00", "room": "Hall B", "level": "Beginner"},
    {"id": 6,  "title": "Chrome DevTools Tips & Tricks",     "speaker": "Jecelyn Yeen",        "track": "Web",     "day": 1, "time": "16:00", "room": "Hall D", "level": "Beginner"},
    {"id": 7,  "title": "Compose Multiplatform",             "speaker": "Lyla Lee",            "track": "Mobile",  "day": 2, "time": "09:00", "room": "Hall C", "level": "Intermediate"},
    {"id": 8,  "title": "LLMs in Production",                "speaker": "Martin Gorner",       "track": "AI & ML", "day": 2, "time": "10:00", "room": "Hall A", "level": "Advanced"},
    {"id": 9,  "title": "Kubernetes Best Practices",         "speaker": "Kelsey Hightower",    "track": "Cloud",   "day": 2, "time": "11:00", "room": "Hall B", "level": "Advanced"},
    {"id": 10, "title": "Web Performance in 2026",           "speaker": "Addy Osmani",         "track": "Web",     "day": 2, "time": "14:00", "room": "Hall D", "level": "Intermediate"},
    {"id": 11, "title": "Security at Google Scale",          "speaker": "Ryan Rix",            "track": "Security","day": 2, "time": "15:00", "room": "Hall E", "level": "Advanced"},
    {"id": 12, "title": "Responsible AI Practices",          "speaker": "Alex Siegman",        "track": "AI & ML", "day": 2, "time": "16:00", "room": "Hall A", "level": "Beginner"},
]


def get_sessions(track=None, day=None, speaker=None):
    sessions = list(SESSIONS)
    if track:
        sessions = filter_by_track(sessions, track)
    if day:
        sessions = filter_by_day(sessions, day)
    if speaker:
        sessions = search_by_speaker(sessions, speaker)
    return sessions


def filter_by_track(sessions, track):
    # BUG 1: normalises the input but sessions store display names as-is.
    # "AI & ML" becomes "ai-and-ml" which never matches "AI & ML".
    normalized = track.lower().replace(" ", "-").replace("&", "and")
    return [s for s in sessions if s["track"] == normalized]


def filter_by_day(sessions, day):
    # BUG 2: sessions store day as int (1, 2) but the param arrives as a string.
    # "1" != 1 in Python - returns empty list for every day.
    return [s for s in sessions if s["day"] == day]


def search_by_speaker(sessions, query):
    # BUG 3: case-sensitive match - "eric" never finds "Eric Schmidt".
    return [s for s in sessions if query in s["speaker"]]


def session_count(sessions):
    # BUG 4: counts from the full SESSIONS list, not the filtered one passed in.
    return len(SESSIONS)
