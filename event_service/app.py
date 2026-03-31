from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import jwt
import redis
from database import get_connection

SECRET_KEY = "super_secret_jwt_key"
redis_client = redis.Redis(host="redis", port=6379, password="redis123", decode_responses=True)

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def check_admin(self):
        auth_header = self.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload.get("role") == "admin"
        except:
            return False

    def do_GET(self):
        if self.path == "/events" or self.path == "/admin/events":
            cached = redis_client.get("events:all")
            if cached:
                self.respond(200, json.loads(cached))
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Title, Description, TotalSeats, AvailableSeats FROM Events")
            events = [
                {"id": r[0], "title": r[1], "description": r[2], "total_seats": r[3], "available_seats": r[4]} 
                for r in cursor.fetchall()
            ]
            conn.close()

            redis_client.setex("events:all", 300, json.dumps(events))
            self.respond(200, events)
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/admin/events":
            if not self.check_admin():
                self.respond(403, {"error": "Admin access required"})
                return

            content_length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(content_length))

            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO Events (Title, Description, TotalSeats, AvailableSeats) VALUES (?, ?, ?, ?)",
                    data["title"], data["description"], data["total_seats"], data["total_seats"]
                )
                conn.commit()
                redis_client.delete("events:all")
                self.respond(201, {"message": "Event created"})
            except Exception as e:
                self.respond(500, {"error": str(e)})
            finally:
                conn.close()

    def respond(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("Event service running on port 8000...")
server.serve_forever()