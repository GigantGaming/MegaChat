from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

Allowed_room = ["Mini", "Hacker", "Mut"]
Room_meb = {}

# NEW: Dictionary to store message history for each room
# Format: {"Mini": [{"username": "Alex", "msg": "Hi!"}], "Hacker": []}
#chat_history = {room: [] for room in Allowed_room}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        room = request.form.get('room')
        
        if username and room:
            session['username'] = username
            session['room'] = room
            return redirect(url_for('chat'))
            
    return render_template('index.html')

@app.route('/chat')
def chat():
    if 'username' not in session or 'room' not in session:
        return redirect(url_for('index'))
    username = session.get('username')
    room = session.get('room')
    if room not in Allowed_room:
        return redirect(url_for("index"))
    return render_template("chat.html", username=username, room=room)

@socketio.on('join')
def handle_join(data):
    global Room_meb # chat_history
    username = session.get('username')
    room = session.get('room')
    
    join_room(room)
    Room_meb[room] = Room_meb.get(room, 0) + 1
    
    # 1. Send past message history ONLY to the user who just joined/refreshed
    #if room in chat_history:
       # emit('load_history', chat_history[room], to=request.sid)

    # 2. Notify OTHERS in the room that a new user joined
    send(f"📢 {username} has joined the chat.", to=room, include_self=False)

    # 3. Update live count for everyone
    emit('update_live_count', {'count': Room_meb[room]}, to=room)

@socketio.on('message')
def handle_message(msg):
    #global chat_history
    username = session.get('username')
    room = session.get('room')
    
    # Structure the message details
    message_data = {"username": username, "msg": msg}
    
    # 1. Save message to history (keeps the last 50 messages to save memory)
    #if room in chat_history:
        #chat_history[room].append(message_data)
        #if len(chat_history[room]) > 50: 
           # chat_history[room].pop(0)

    # 2. Broadcast the formatted message to the entire room
    formatted_msg = f"{username}: {msg}"
    send(formatted_msg, to=room)

@socketio.on('disconnect')
def handle_disconnect(reason=None):
    global Room_meb
    username = session.get('username')
    room = session.get('room')

    if username and room:
        leave_room(room)
        if room in Room_meb and Room_meb[room] > 0:
            Room_meb[room] -= 1
        send(f"🚪 {username} has left the chat.", to=room)
        emit('update_live_count', {'count': Room_meb[room]}, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
    
