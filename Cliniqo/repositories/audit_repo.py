from db.connection import DBConn
from typing import Optional


class AuditRepository:

    def log(self, user_id: Optional[int], action: str,
            table_name: str, record_id: Optional[int],
            details: str = None, ip_address: str = None):
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO audit_logs
                        (user_id, action, table_name, record_id, details, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, action, table_name, record_id, details, ip_address))

    def get_recent(self, limit: int = 50):
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT al.id, u.name, al.action, al.table_name,
                           al.record_id, al.details, al.created_at
                    FROM audit_logs al
                    LEFT JOIN users u ON u.id = al.user_id
                    ORDER BY al.created_at DESC
                    LIMIT %s
                """, (limit,))
                cols = ['id','user','action','table','record_id','details','timestamp']
                return [dict(zip(cols, row)) for row in cur.fetchall()]
