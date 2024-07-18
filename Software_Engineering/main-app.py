import os
from random import choice
import random
import re
import string
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_socketio import emit, join_room, send, SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from collections import defaultdict

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '12345'
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
app.app_context().push()

active_users_in_rooms = {}
votes = defaultdict(lambda: {'yes': 0, 'no': 0})
user_votes = defaultdict(lambda: {})

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    
    rooms = db.relationship('UserRoom', back_populates='user')


def list_files_in_folder(folder_path):
    file_names = []

    items = os.listdir(folder_path)

    for item in items:
        if os.path.isfile(os.path.join(folder_path, item)):

            file_names.append(item)

    return file_names


def get_random_file(folder_path):

    file_paths = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return random.choice(file_paths) if file_paths else None


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), nullable=False )
    members = db.relationship('UserRoom', back_populates='room')

    music_path = db.Column(db.Text(), nullable=False)

    def __init__(self, code) -> None:
        self.code = code
        self.music_path = get_random_file('static/media')


class UserRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    user = db.relationship('User', back_populates='rooms')
    room = db.relationship('Room', back_populates='members')

    def __init__(self, user, room) -> None:
        self.user = user
        self.room = room

# with app.app_context():
#     db.create_all()


class RegisterFrom(FlaskForm):
    username = StringField(validators=[InputRequired(), 
                Length(min=4, max=20)], render_kw={"placeholder": "username"})
   
    password = StringField(validators=[InputRequired(), 
                 Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_name = User.query.filter_by(username=username.data).first()

        if existing_user_name:
            raise ValidationError('Username already exist')


class LoginFrom(FlaskForm):
    username = StringField(validators=[InputRequired(), 
                Length(min=4, max=20)], render_kw={"placeholder": "username"})
   
    password = StringField(validators=[InputRequired(), 
                 Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    
    submit = SubmitField('Login')


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginFrom()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('lobby'))
            
    return render_template('login.html',form=form)


@app.route('/lobby', methods=['GET', 'POST'])
@login_required
def lobby():
    rooms = [{
        "code" : user_room.room.code, 
        "music_path" : url_for('static', filename=f'media/{user_room.room.music_path}')  
    } for user_room in current_user.rooms]

    return render_template('lobby.html', room_codes = rooms)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register',  methods=['GET', 'POST'])
def register():
    form = RegisterFrom()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


@app.get('/add_room')
def add_room():
    print('called')
    def create_code():
        letter = lambda: choice(string.ascii_lowercase)
        return '-'.join(letter() for _ in range(9) )
    
    while True:
        new_code = create_code()
        room_exists = Room.query.filter_by(code = new_code).first()
        if room_exists is None:
            room = Room(code = new_code)
            user_room = UserRoom(current_user, room)
            db.session.add(room)
            db.session.add(user_room)
            db.session.commit()
            reset_votes(new_code)

            return jsonify({
                'code': new_code,
                "music_path" : url_for('static', filename=f'media/{user_room.room.music_path}')
            })
        
    

@app.route('/room_details/<room_code>', methods=['GET'])
def room_details(room_code):
    if not re.match(r'^[a-z]-[a-z]-[a-z]-[a-z]-[a-z]-[a-z]-[a-z]-[a-z]-[a-z]$', room_code):
        return "Invalid room code format.", 400

    room = Room.query.filter_by(code=room_code).first()
    if room:
        return jsonify({
            'code': room.code,
            'music_path': url_for('static', filename=f'media/{room.music_path}')
        })
    else:
        return "Room not found.", 404


@socketio.on('join')
def handle_join(data):
    room_code = data['room']
    join_room(room_code)

    room = Room.query.filter_by(code=room_code).first()
    if not room:
        room = Room(code=room_code, music_path='default.mp3')  # Adjust as needed
        db.session.add(room)
        db.session.commit()

    join_room(room_code)

    user_room = UserRoom.query.filter_by(user_id=current_user.id, room_id=room.id).first()
    if not user_room:
        user_room = UserRoom(user_id=current_user.id, room_id=room.id)
        db.session.add(user_room)
        db.session.commit()

    if room_code not in active_users_in_rooms:
        active_users_in_rooms[room_code] = set()
    
    active_users_in_rooms[room_code].add(current_user.id)
    
    send(f"{current_user.username} has joined the room.", room=room_code)

    reset_votes(room_code)


@socketio.on('connect')
def handle_connect():
    user_rooms = UserRoom.query.filter_by(user_id=current_user.id).all()
    for user_room in user_rooms:
        room = Room.query.get(user_room.room_id)
        if room:
            join_room(room.code)
            if room.code not in active_users_in_rooms:
                active_users_in_rooms[room.code] = set()
            active_users_in_rooms[room.code].add(current_user.id)
            send(f"{current_user.username} has rejoined the room.", room=room.code)


@socketio.on('disconnect')
def handle_disconnect():
    for room_code in active_users_in_rooms.keys():
        active_users_in_rooms[room_code].discard(current_user.id)


@socketio.on('rejoin_rooms')
def handle_rejoin_rooms(data):
    print("Received rejoin_rooms event")
    user_rooms = UserRoom.query.filter_by(user_id=current_user.id).all()
    for user_room in user_rooms:
        room = Room.query.get(user_room.room_id)
        if room:
            join_room(room.code)
            if room.code not in active_users_in_rooms:
                active_users_in_rooms[room.code] = set()
            active_users_in_rooms[room.code].add(current_user.id)
            send(f"{current_user.username} has rejoined the room.", room=room.code)


def reset_votes(room_code):
    votes[room_code] = {'yes': 0, 'no': 0}
    user_votes[room_code] = {}


@socketio.on('vote_to_skip')
def handle_vote_to_skip(data):
    room_code = data['room']
    vote = data['vote']
    user_id = current_user.id

    if room_code not in votes:
        votes[room_code] = {'yes': 0, 'no': 0}
        user_votes[room_code] = {}

    if user_id in user_votes[room_code]:
        emit('vote_received', {'vote': vote, 'status': 'already_voted'})
        return

    user_votes[room_code][user_id] = vote
    votes[room_code][vote] += 1

    total_votes = votes[room_code]['yes'] + votes[room_code]['no']
    users_in_room = len(active_users_in_rooms.get(room_code, []))

    MINIMUM_VOTES_REQUIRED = 2

    emit('vote_count_update', {
        'yes': votes[room_code]['yes'],
        'no': votes[room_code]['no']
    }, room=room_code)

    if total_votes >= MINIMUM_VOTES_REQUIRED:
        if votes[room_code]['yes'] > users_in_room / 2:
            new_song_path = url_for('static', filename=f'media/{get_random_file("static/media")}')
            emit('skip_song', {'music_path': new_song_path}, room=room_code)
            reset_votes(room_code)
        elif votes[room_code]['no'] >= users_in_room / 2:
            emit('no_skip', room=room_code)
            reset_votes(room_code)
    else:
        emit('vote_received', {
            'vote': vote, 
            'status': 'pending',
            'message': f"Waiting for more votes. Total votes: {total_votes}/{MINIMUM_VOTES_REQUIRED}."
        })


if __name__ == '__main__':
    socketio.run(app, debug=True)
