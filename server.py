import json
import os
import socket
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'responses.json')
_lock = threading.Lock()

# ── 資料存取 ──────────────────────────────────────────────────

def read_responses():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_responses(responses):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)

VALID_VALUES = {'yes', 'maybe', 'no'}
VALID_DATE_IDS = {f'd{i}' for i in range(1, 22)}

def validate_and_clean(data: dict) -> dict | None:
    name = str(data.get('name', '')).strip()[:50]
    if not name:
        return None
    raw_sel = data.get('selections', {})
    if not isinstance(raw_sel, dict):
        return None
    selections = {
        k: v for k, v in raw_sel.items()
        if k in VALID_DATE_IDS and v in VALID_VALUES
    }
    notes = str(data.get('notes', '')).strip()[:500]
    return {'name': name, 'selections': selections, 'notes': notes,
            'ts': datetime.now().isoformat()}

# ── HTTP handler ──────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):   # 簡化 console log
        print(f"  {self.address_string()} {fmt % args}")

    def _send(self, code, body, content_type='application/json'):
        data = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/':
            self._serve_file('index.html', 'text/html')
        elif self.path == '/api/responses':
            with _lock:
                data = read_responses()
            self._send(200, json.dumps(data, ensure_ascii=False))
        else:
            self._send(404, '{"error":"not found"}')

    def do_POST(self):
        if self.path != '/api/response':
            self._send(404, '{"error":"not found"}')
            return
        length = int(self.headers.get('Content-Length', 0))
        try:
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._send(400, '{"error":"invalid JSON"}')
            return
        entry = validate_and_clean(body)
        if entry is None:
            self._send(400, '{"error":"invalid data"}')
            return
        with _lock:
            responses = read_responses()
            responses.append(entry)
            write_responses(responses)
        self._send(200, json.dumps({'ok': True, 'total': len(responses)}))

    def do_DELETE(self):
        if self.path != '/api/responses':
            self._send(404, '{"error":"not found"}')
            return
        with _lock:
            write_responses([])
        self._send(200, '{"ok":true}')

    def _serve_file(self, filename, content_type):
        path = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(path):
            self._send(404, '{"error":"file not found"}')
            return
        with open(path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

# ── 啟動 ──────────────────────────────────────────────────────

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

if __name__ == '__main__':
    PORT = 8080
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    local_ip = get_local_ip()
    print('=' * 50)
    print('  ✈️  部門旅遊意願調查伺服器已啟動')
    print('=' * 50)
    print(f'  本機訪問：http://localhost:{PORT}')
    print(f'  區域網路：http://{local_ip}:{PORT}')
    print(f'\n  將上方區域網路網址分享給同事即可！')
    print(f'  資料存檔：{DATA_FILE}')
    print('\n  Ctrl+C 停止伺服器\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n伺服器已停止。')
