from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import jwt
import redis
import pika
from database import get_connection

SECRET_KEY = "super_secret_jwt_key"
redis_client = redis.Redis(host="redis", port=6379, password="redis123", decode_responses=True)

def send_to_rabbitmq(message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='notifications', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='notifications',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
    except Exception as e:
        print("RabbitMQ Error:", e)

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def get_user_from_token(self):
        auth_header = self.headers.get("Authorization")
        if not auth_header: return None
        try:
            token = auth_header.split(" ")[1]
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except:
            return None

    def do_GET(self):
        user_payload = self.get_user_from_token()
        
        if self.path == "/admin/bookings":
            if not user_payload or user_payload.get("role") != "admin":
                self.respond(403, {"error": "Admin access required"})
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Id, UserId, EventId, Status FROM Bookings")
            bookings = [{"id": r[0], "user_id": r[1], "event_id": r[2], "status": r[3]} for r in cursor.fetchall()]
            conn.close()
            self.respond(200, bookings)

        elif self.path == "/admin/logs":
            if not user_payload or user_payload.get("role") != "admin":
                self.respond(403, {"error": "Admin access required"})
                return
            
            logs_raw = redis_client.lrange("system_logs", 0, -1)
            logs = [json.loads(l) for l in logs_raw]
            self.respond(200, logs)
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/bookings":
            user_payload = self.get_user_from_token()
            if not user_payload:
                self.respond(401, {"error": "Unauthorized"})
                return

            content_length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(content_length))
            event_id = data["event_id"]
            user_id = user_payload["user_id"]

            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT AvailableSeats FROM Events WHERE Id = ?", event_id)
            event = cursor.fetchone()
            
            if not event or event[0] <= 0:
                conn.close()
                self.respond(400, {"error": "No available seats"})
                return

            try:
                cursor.execute("UPDATE Events SET AvailableSeats = AvailableSeats - 1 WHERE Id = ?", event_id)
                cursor.execute("INSERT INTO Bookings (UserId, EventId, Status) VALUES (?, ?, 'CONFIRMED')", user_id, event_id)
                conn.commit()
                
                redis_client.delete("events:all")

                send_to_rabbitmq({
                    "type": "BOOKING_CREATED",
                    "user_id": user_id,
                    "event_id": event_id
                })

                self.respond(201, {"message": "Booking successful"})
            except Exception as e:
                self.respond(500, {"error": str(e)})
            finally:
                conn.close()
        else:
            self.respond(404, {"error": "Not found"})

    def respond(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("Booking service running on port 8000...")
server.serve_forever()