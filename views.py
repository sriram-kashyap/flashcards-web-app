from logging import log
from re import S
from flask import Blueprint, render_template, request, flash, send_file
from flask_login import login_user, logout_user, current_user
from flask_login.utils import login_required
from werkzeug.utils import redirect
from models import User, Deck, Card, Export
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from datetime import datetime
import csv
from io import BytesIO
import os

views = Blueprint("views", __name__)

BASE = 'http://127.0.0.1:5000'


@views.route('/dashboard', methods = ['GET', 'POST'])
@login_required
def home():
    time = datetime.now()
    current_user.last_rev=time
    db.session.commit()
    data = requests.get(BASE+f'/api/deck/{current_user.username}')
    return render_template('dashboard.html', decks=data.json(), user=current_user.username)

@views.route('/', methods=['GET'])
def landing():
    return render_template('landing.html')


@views.route('/review/<string:deck>', methods = ['GET', 'POST'])
@login_required
def review(deck):
    time = datetime.now()
    d=Deck.query.filter_by(deck_name=deck).first()
    d.last_rev=time
    db.session.commit()
    data=requests.get(BASE+ f'/api/{current_user.username}/{deck}/card')

    if data:
        return render_template('review.html', front = data.json()['front'], back = data.json()['back'], deck=data.json()['deck'], card_id=data.json()['card_id'])
    else:
        return render_template('review.html', front = 'No cards yet, Add cards to get started', deck=deck)

@views.route('/review/<string:deck>/<int:card_id>', methods = ['GET', 'POST'])
def score(deck,card_id):
    if request.method == 'POST':
        c = Card.query.filter_by(card_id=card_id).first()
        s = int(request.form.get('score'))
        c.score = s
        db.session.commit()
        d= Deck.query.filter_by(deck_name=deck, user=current_user.username).first()
        cn = Card.query.filter_by(deck=deck).count()
        d.score = ((d.score+c.score)/cn)
        db.session.commit()
        return redirect(f'/review/{deck}')

@views.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect('/dashboard')
            else:
                flash('Password is incorrect.', category='error')
        else:
            flash('Username does not exist.', category='error')

    return render_template('login.html')


@views.route('/register', methods = ['GET', 'POST'])
def register():
    return render_template('register.html')


@views.route('/<string:user>/deck/<string:deck>/delete', methods=['GET','POST'])
def deletedeck(deck, user):
    d= Deck.query.filter_by(deck_name=deck, user=user).first()
    db.session.delete(d)
    db.session.commit()
    return redirect('/dashboard')

@views.route("/<string:user>/deck/<string:deck>/export", methods=["GET","POST"])
def export(deck, user):
    cards = Card.query.filter_by(deck=deck)
    card_list=[["Card_ID", "DECK", "FRONT", "BACK"]]
    for card in cards:
        new_card = [card.card_id, card.deck, card.front, card.back]
        card_list.append(new_card)     

    filename = deck+".csv"
    file = open(filename, 'w', newline='')
    writer = csv.writer(file)
    writer.writerows(card_list)
    file.close()
    file = open(filename, 'r')
    upload = Export(filename=filename, data=bytes(file.read(), encoding='utf-8'))
    db.session.add(upload)
    db.session.commit()
    return send_file(BytesIO(upload.data), attachment_filename=upload.filename, as_attachment=True)

@views.route("/download/<upload_id>")    

@views.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')
