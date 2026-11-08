#!/usr/bin/env python3
"""
Lightweight Web Viewer for Synthetic EHR Data.
Run this script and open http://localhost:8501 in your browser to view all tables visually.
"""
import http.server
import json
import sqlite3
import urllib.parse

PORT = 8501
DB_PATH = "synthea_data.db"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Synthetic EHR Data Viewer</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #f8fafc; color: #1e293b; }
        h1 { margin-top: 0; color: #0f172a; display: flex; align-items: center; gap: 10px; }
        .container { display: flex; gap: 20px; }
        .sidebar { width: 220px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .sidebar h3 { margin-top: 0; font-size: 14px; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px; }
        .table-btn { display: block; width: 100%; text-align: left; padding: 8px 12px; margin-bottom: 5px; border: none; background: transparent; border-radius: 6px; cursor: pointer; font-size: 14px; color: #334155; }
        .table-btn:hover { background: #f1f5f9; color: #0284c7; }
        .table-btn.active { background: #e0f2fe; color: #0284c7; font-weight: 600; }
        .main { flex: 1; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow-x: auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
        th { background: #f8fafc; padding: 10px 12px; border-bottom: 2px solid #e2e8f0; color: #475569; position: sticky; top: 0; white-space: nowrap; }
        td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; white-space: nowrap; max-width: 300px; overflow: hidden; text-overflow: ellipsis; }
        tr:hover { background: #f8fafc; }
        .badge { background: #0284c7; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
    </style>
</head>
<body>
    <h1>🏥 Synthetic EHR Data Viewer <span class="badge" id="record-count">Loading...</span></h1>
    <div class="container">
        <div class="sidebar">
            <h3>Clinical Tables</h3>
            <div id="table-list"></div>
        </div>
        <div class="main">
            <div class="header-bar">
                <h2 id="current-table-title" style="margin:0;">Select a table</h2>
            </div>
            <div id="table-container">Loading...</div>
        </div>
    </div>

    <script>
        let currentTable = 'patients';

        async function fetchTables() {
            const res = await fetch('/api/tables');
            const tables = await res.json();
            const listEl = document.getElementById('table-list');
            listEl.innerHTML = '';
            tables.forEach(t => {
                const btn = document.createElement('button');
                btn.className = 'table-btn' + (t === currentTable ? ' active' : '');
                btn.innerText = t;
                btn.onclick = () => loadTable(t);
                listEl.appendChild(btn);
            });
            loadTable(currentTable);
        }

        async function loadTable(table) {
            currentTable = table;
            document.querySelectorAll('.table-btn').forEach(b => {
                b.className = 'table-btn' + (b.innerText === table ? ' active' : '');
            });
            document.getElementById('current-table-title').innerText = table.toUpperCase() + ' (Top 50 Rows)';
            const res = await fetch('/api/data?table=' + encodeURIComponent(table));
            const data = await res.json();
            
            document.getElementById('record-count').innerText = data.total + ' total records';

            if (!data.rows || data.rows.length === 0) {
                document.getElementById('table-container').innerHTML = '<p>No data found.</p>';
                return;
            }

            let html = '<table><thead><tr>';
            data.columns.forEach(c => html += '<th>' + c + '</th>');
            html += '</tr></thead><tbody>';
            data.rows.forEach(r => {
                html += '<tr>';
                r.forEach(val => html += '<td title="' + (val === null ? '' : val) + '">' + (val === null ? '<span style="color:#cbd5e1">null</span>' : val) + '</td>');
                html += '</tr>';
            });
            html += '</tbody></table>';
            document.getElementById('table-container').innerHTML = html;
        }

        fetchTables();
    </script>
</body>
</html>
"""

class EHRRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/tables":
            conn = sqlite3.connect(DB_PATH)
            tables = [r[0] for r in conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
            conn.close()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(tables).encode("utf-8"))
        elif parsed.path == "/api/data":
            query = urllib.parse.parse_qs(parsed.query)
            table = query.get("table", ["patients"])[0]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute(f"SELECT * FROM [{table}] LIMIT 50")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                total = cursor.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
                resp = {"columns": columns, "rows": rows, "total": total}
            except Exception as e:
                resp = {"columns": [], "rows": [], "total": 0, "error": str(e)}
            conn.close()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), EHRRequestHandler)
    print(f"🚀 Synthetic EHR Web Viewer running at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
