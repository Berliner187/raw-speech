import sqlite3
import os
from datetime import datetime

class DB:
    def __init__(self):
        path = os.path.expanduser("~/Library/Application Support/BoltAI")
        os.makedirs(path, exist_ok=True)
        self.conn = sqlite3.connect(os.path.join(path, "history.db"), check_same_thread=False)

        try:
            self.conn.execute("ALTER TABLE history ADD COLUMN audio_len REAL DEFAULT 0")
            self.conn.execute("ALTER TABLE history ADD COLUMN proc_len REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        self.conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, text TEXT, dt DATETIME, audio_len REAL, proc_len REAL)")

    def add(self, text, audio_len, proc_len):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(f"INSERT INTO history (text, dt, audio_len, proc_len) VALUES (?, datetime('{now}'), ?, ?)", 
                         (text, audio_len, proc_len))
        self.conn.commit()

    def get_all(self):
        return self.conn.execute("SELECT text, dt FROM history ORDER BY id DESC LIMIT 50").fetchall()

    def get_stats(self):
        row = self.conn.execute("SELECT COUNT(*), SUM(LENGTH(text)), SUM(audio_len), AVG(audio_len/NULLIF(proc_len, 0)) FROM history").fetchone()
        count = row[0] or 0
        chars = row[1] or 0
        total_audio_sec = row[2] or 0
        avg_speed = row[3] or 0
        
        first = self.conn.execute("SELECT MIN(dt) FROM history").fetchone()[0]
        days = 1
        if first:
            try:
                delta = datetime.now() - datetime.strptime(first, '%Y-%m-%d %H:%M:%S')
                days = max(1, delta.days)
            except: pass

        return {
            "count": count,
            "chars": chars,
            "words": chars // 6,
            "hours": round(chars / 12000, 2),
            "speed_factor": round(avg_speed, 1),
            "total_audio_min": round(total_audio_sec / 60, 1),
            "avg_len": chars // count if count > 0 else 0,
            "intensity": round(count / days, 1)
        }
    
    def delete_entry(self, dt):
        self.conn.execute("DELETE FROM history WHERE dt = ?", (dt,))
        self.conn.commit()
    
    def get_weekly_activity(self):
        res = self.conn.execute("""
            SELECT date(dt), SUM(LENGTH(text)) FROM history 
            WHERE dt >= date('now', '-7 days')
            GROUP BY date(dt) ORDER BY date(dt) ASC
        """).fetchall()
        stats = {d: c for d, c in res}
        from datetime import datetime, timedelta
        return [stats.get((datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), 0) for i in range(6, -1, -1)]
    
    def get_all_full(self):
        return self.conn.execute("SELECT text, dt, COALESCE(audio_len, 0), COALESCE(proc_len, 0) FROM history ORDER BY id DESC LIMIT 50").fetchall()

    def search(self, query):
        q = f"%{query}%"
        return self.conn.execute("SELECT text, dt, COALESCE(audio_len, 0), COALESCE(proc_len, 0) FROM history WHERE text LIKE ? ORDER BY id DESC", (q,)).fetchall()
    
    def get_models(self):
        return [
            {"id": "turbo", "name": "Whisper Turbo", "desc": "Баланс между скоростью и качеством.", "speed": 95, "acc": 85, "active": True},
            {"id": "small", "name": "Whisper Small", "desc": "Максимальная скорость. Идеально для чипов M-серии.", "speed": 70, "acc": 75, "active": False},
            {"id": "large", "name": "Whisper Large", "desc": "Максимальная точность, но ниже скорость.", "speed": 30, "acc": 98, "active": False},
        ]
