import sqlite3
import json
conn = sqlite3.connect('c:/Users/j_sco/projects/Milo/Milo/checkpoints.sqlite')
c = conn.cursor()
c.execute('SELECT channel_values FROM checkpoints ORDER BY thread_id DESC LIMIT 1')
row = c.fetchone()
if row:
    data = json.loads(row[0].decode('utf-8') if isinstance(row[0], bytes) else row[0])
    print(str(data)[:2000])
