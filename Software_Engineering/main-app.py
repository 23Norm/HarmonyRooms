import os
from random import choice
import random
import string
from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '12345'
db = SQLAlchemy(app)
app.app_context().push()

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

    file_paths = list_files_in_folder(folder_path)

    if file_paths:
        return random.choice(file_paths)
    else:
        return "Folder is empty."

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), nullable=False )
    members = db.relationship('UserRoom', back_populates='room')

    music_path = db.Column(db.Text(), nullable=False)

    def __init__(self, code) -> None:
        self.code = code
        self.music_path = get_random_file('static/media')

# model vote
# 

    
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

            return jsonify({
                'code': new_code,
                "music_path" : url_for('static', filename=f'media/{user_room.room.music_path}')
            })

if __name__ == '__main__':
    app.run(debug=True)