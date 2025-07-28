import sqlite3
import pandas as pd

conn = sqlite3.connect('db/agg_result.db')

# sql
query = """
SELECT user_id, SUM(total_volume) as total_volume, SUM(total_pnl) as total_pnl
FROM agg_trades_weekly
WHERE LOWER(client_type) = 'bronze'
-- for only profitable clients use below
-- WHERE LOWER(client_type) = 'bronze' AND total_pnl > 0
GROUP BY user_id
ORDER BY total_volume DESC
LIMIT 3
"""

df = pd.read_sql(query, conn)

df.to_excel('reports/top_clients.xlsx', index=False)