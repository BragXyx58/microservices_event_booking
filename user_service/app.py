from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import hashlib
import jwt
import datetime
import redis
from database import get_connection

SECRET_KEY = "super_secret_jwt_key"

redis_client = redis.Redis(host="redis", port=6379, password="redis123", decode_responses=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def check_admin(self):
        auth_header = self.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload.get("role") == "admin"
        except:
            return False

    def do_GET(self):
        if self.path == "/admin/users":
            if not self.check_admin():
                self.respond(403, {"error": "Access denied"})
                return
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Username, Role FROM Users")
            users = [{"id": row[0], "username": row[1], "role": row[2]} for row in cursor.fetchall()]
            conn.close()
            self.respond(200, users)
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        if self.path == "/register":
            self.register(data)
        elif self.path == "/login":
            self.login(data)

    def register(self, data):
        conn = get_connection()
        cursor = conn.cursor()
        username = data["username"]
        hashed = hash_password(data["password"])
        role = data.get("role", "user") 

        try:
            cursor.execute("INSERT INTO Users (Username, PasswordHash, Role) VALUES (?, ?, ?)", username, hashed, role)
            conn.commit()
            self.respond(200, {"message": "registered"})
        except Exception as e:
            self.respond(500, {"error": str(e)})
        finally:
            conn.close()

    def login(self, data):
        conn = get_connection()
        cursor = conn.cursor()
        username = data["username"]
        hashed = hash_password(data["password"])

        cursor.execute("SELECT Id, Role FROM Users WHERE Username = ? AND PasswordHash = ?", username, hashed)
        row = cursor.fetchone()
        conn.close()

        if not row:
            self.respond(401, {"error": "invalid credentials"})
            return

        user_id, role = row[0], row[1]
        
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        
        self.respond(200, {"token": token, "role": role})

    def respond(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("User service running on port 8000...")
server.serve_forever()