from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
from mysql import ChatDatabase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")
db = ChatDatabase()
db.setup_database()
online_users = 0


# 1. Login Page / Username Request
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        room = request.form.get('room') # Users can pick a group room
        
        if username and room:
            session['username'] = username
            session['room'] = room
            return redirect(url_for('chat'))
            
    return render_template('index.html')

# 2. Chat Room Page
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat1.html', username=session['username'], room=session['room'])

# 3. Socket.IO Events
@socketio.on('join')
def handle_join(data):
    username = session.get('username')
    room = session.get('room')
    global online_users
    online_users += 1
    
    join_room(room)
    # Notify others in the room
    send(f"🔴Live: {online_users}")
    send(f"📢 {username} has joined the chat.", to=room)
    history = db.get_recent_messages()
    for message in history:
      send(f"{message["sender"]}: {message["message"]}")

#... keep your existing routes and events... to show whenever anyone leave from room
@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    room = session.get('room')
  
    global online_users
    online_users -= 1
    if online_users < 0 :
      online_users = 0

    if username and room:
        leave_room(room)
        # Notify others in the room that the user left from room
        send(f"🔴Live: {online_users}")
        send(f"🚪 {username} has left the chat.", to=room)

@socketio.on('message')
def handle_message(msg):
    username = session.get('username')
    room = session.get('room')
    
    # Format message with username and broadcast only to the specific room
    formatted_msg = f"{username}: {msg}"
    send(formatted_msg, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
  
