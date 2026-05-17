import sqlite3
import os
from datetime import datetime

class DB:
    def __init__(self):
        path = os.path.expanduser("~/Library/Application Support/BoltAI")
        os.makedirs(path, exist_ok=True)
        self.conn = sqlite3.connect(os.path.join(path, "history.db"), check_same_thread=False)

        self.conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, dt DATETIME, audio_len REAL, proc_len REAL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")

        try:
            self.conn.execute("ALTER TABLE history ADD COLUMN audio_len REAL DEFAULT 0")
            self.conn.execute("ALTER TABLE history ADD COLUMN proc_len REAL DEFAULT 0")
        except: pass

        try:
            self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS history_fts USING fts5(text, dt UNINDEXED, audio_len UNINDEXED, proc_len UNINDEXED, tokenize='unicode61')")
        except:
            print("FTS5 не поддерживается системой, будем юзать LIKE.")

    def add(self, text, audio_len, proc_len):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute("INSERT INTO history (text, dt, audio_len, proc_len) VALUES (?, ?, ?, ?)", (text, now, audio_len, proc_len))
        try:
            self.conn.execute("INSERT INTO history_fts (text, dt, audio_len, proc_len) VALUES (?, ?, ?, ?)", (text, now, audio_len, proc_len))
        except: pass
        self.conn.commit()

    def search(self, query):
        if not query or not query.strip():
            return self.get_all_full()

        try:
            clean_q = " ".join([f"{w}*" for w in query.split() if w])
            res = self.conn.execute("SELECT text, dt, audio_len, proc_len FROM history_fts WHERE text MATCH ? ORDER BY rank", (clean_q,)).fetchall()
            if res: return res
        except: pass

        words = [w for w in query.split() if w]
        sql = "SELECT text, dt, audio_len, proc_len FROM history WHERE text LIKE ? ORDER BY id DESC LIMIT 100"
        params = [f"%{query}%"]
        return self.conn.execute(sql, params).fetchall()

    def get_stats(self):
        row = self.conn.execute("""
            SELECT 
                COUNT(*), 
                SUM(LENGTH(text)), 
                SUM(COALESCE(audio_len, 0)), 
                AVG(COALESCE(audio_len/NULLIF(proc_len, 0), 1)) 
            FROM history
        """).fetchone()
        
        count = row[0] or 0
        chars = row[1] or 0
        total_sec = row[2] or 0
        avg_speed = row[3] or 0
        
        audio_min = total_sec / 60
        wpm = round((chars // 6) / audio_min) if audio_min > 0.1 else 0

        dates = self.conn.execute("SELECT DISTINCT date(dt) FROM history WHERE dt IS NOT NULL ORDER BY date(dt) DESC LIMIT 30").fetchall()
        streak = 0
        if dates:
            from datetime import date, timedelta
            for i, d_row in enumerate(dates):
                if d_row[0] is None: continue
                try:
                    d = datetime.strptime(str(d_row[0]), '%Y-%m-%d').date()
                    if d == date.today() - timedelta(days=i): streak += 1
                    else: break
                except: continue

        return {
            "count": count, "hours": round(chars / 12000, 2), "speed_factor": round(avg_speed, 1),
            "wpm": wpm, "streak": streak, "total_audio_min": round(audio_min, 1), "avg_len": chars // count if count > 0 else 0,
            "intensity": round(count / 1, 1)
        }

    def delete_entry(self, dt):
        self.conn.execute("DELETE FROM history WHERE dt = ?", (dt,))
        try: self.conn.execute("DELETE FROM history_fts WHERE dt = ?", (dt,))
        except: pass
        self.conn.commit()

    def get_all_full(self):
        return self.conn.execute("SELECT text, dt, audio_len, proc_len FROM history ORDER BY id DESC LIMIT 100").fetchall()

    def get_weekly_activity(self):
        res = self.conn.execute("SELECT date(dt), SUM(LENGTH(text)) FROM history WHERE dt >= date('now', '-7 days') GROUP BY date(dt)").fetchall()
        stats = {d: c for d, c in res}
        from datetime import date, timedelta
        return [stats.get((date.today() - timedelta(days=i)).strftime('%Y-%m-%d'), 0) for i in range(6, -1, -1)]

    def get_active_model(self):
        row = self.conn.execute("SELECT value FROM settings WHERE key = 'active_model'").fetchone()
        return row[0] if row else os.path.expanduser("~/Library/Application Support/BoltAI/models/turbo")

    def set_active_model(self, path):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_model', ?)", (path,))
        self.conn.commit()

    def get_models(self):
        bp = os.path.expanduser("~/Library/Application Support/BoltAI/models")
        models = [
            {"id": "turbo", "repo": "mlx-community/whisper-large-v3-turbo", "name": "Whisper Turbo", "size": "1.6 GB", "speed": 98, "acc": 92, "desc": "Баланс скорости и качества."},
            {"id": "medium", "repo": "mlx-community/whisper-medium-mlx-8bit", "name": "Whisper Medium", "size": "770 MB", "speed": 60, "acc": 95, "desc": "Для длинных лекций."},
            {"id": "small", "repo": "mlx-community/whisper-small-mlx", "name": "Whisper Small", "size": "480 MB", "speed": 85, "acc": 75, "desc": "Легкая и быстрая."},
            {"id": "base", "repo": "mlx-community/whisper-base-mlx", "name": "Whisper Base", "size": "145 MB", "speed": 98, "acc": 65, "desc": "Минимум веса."}
        ]
        for m in models:
            m['path'] = os.path.join(bp, m['id'])
            m['downloaded'] = os.path.exists(m['path'])
        return models
