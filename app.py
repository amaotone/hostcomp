import logging
import os
import sqlite3

import pandas as pd
from flask import Flask, flash, g, jsonify, make_response, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sklearn.metrics import mean_absolute_error

app = Flask(__name__)
app.secret_key = 'hostcompsecret'
db_uri = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(app.root_path, 'hostcomp.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'admin')
db = SQLAlchemy(app)

testdata = None


class Score(db.Model):
    __tablename__ = 'scores'
    name = db.Column(db.String(), primary_key=True)
    public = db.Column(db.Float, nullable=False)
    private = db.Column(db.Float, nullable=False)


class Competition(db.Model):
    __tablename__ = 'competitions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    disclose_private = db.Column(db.Boolean, nullable=False)


@app.route('/')
def index():
    compe = Competition.query.first()
    scores = get_scores(private=False)
    return render_template('index.html', title='public leaderboard', scores=scores,
                           compe=compe, private=False)


@app.route('/private')
def private():
    compe = Competition.query.first()
    if not session.get('logged_in') and not compe.disclose_private:
        return redirect(url_for('login'))

    scores = get_scores(private=True)
    return render_template('index.html', title='private leaderboard', scores=scores,
                           compe=compe, private=True)


def get_scores(private=False):
    scores = Score.query.all()
    if private:
        scores = sorted(scores, key=lambda x: x.private)
    else:
        scores = sorted(scores, key=lambda x: x.public)
    return scores


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('admin'))
    error = None
    if request.method == 'POST':
        if request.form['password'] != app.config['ADMIN_PASSWORD']:
            error = 'Incorrect Password'
        else:
            session['logged_in'] = True
            return redirect(url_for('admin'))
    compe = Competition.query.first()
    return render_template('login.html', title='Login', compe=compe, error=error)


@app.route('/admin')
def admin():
    compe = Competition.query.first()
    return render_template('admin.html', title='Admin', compe=compe)


@app.route('/admin/config', methods=['POST'])
def update_config():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))

    compe = Competition.query.first()
    compe.name = request.form['name']
    compe.disclose_private = request.form['disclose_private'] == 'true'
    db.session.add(compe)
    db.session.commit()
    flash('Successfully Updated')
    return redirect(url_for('admin'))


@app.route('/submit', methods=['POST'])
def submit():
    download_dataset()
    if request.headers['Content-Type'] != 'application/json':
        resp = jsonify({'message': f"Invalid Content-Type: {request.headers['Content-Type']}"})
        resp.status_code = 400
        return resp

    data = request.json

    if 'name' not in data:
        resp = jsonify({'message': 'You must specify the name.'})
        resp.status_code = 400
        return resp

    name = data['name']
    pred = list(map(float, data['pred']))

    if len(pred) != len(testdata):
        resp = jsonify({'message': f"Invalid prediction size. len(pred) must be {len(testdata)}, but len(pred) = {len(pred)}."})
        resp.status_code = 422
        return resp

    testdata['pred'] = pred
    public_score = mean_absolute_error(testdata['target'], testdata['pred'], (testdata['private'] == 0).astype(float))
    private_score = mean_absolute_error(testdata['target'], testdata['pred'], (testdata['private'] == 1).astype(float))

    score = Score()
    score.name = name
    score.public = public_score
    score.private = private_score
    db.session.merge(score)
    db.session.commit()

    resp = jsonify({'name': name, 'public_score': public_score})
    resp.status_code = 200
    return resp


@app.route('/delete', methods=['POST'])
def delete():
    if request.headers['Content-Type'] != 'application/json':
        resp = jsonify({'message': f"Invalid Content-Type: {request.headers['Content-Type']}"})
        resp.status_code = 400
        return resp

    data = request.json

    if 'name' not in data:
        resp = jsonify({'message': 'You must specify the name.'})
        resp.status_code = 400
        return resp

    name = data['name']
    score = Score.query.filter_by(name=name).first()

    if not score:
        resp = jsonify({'message': f"Requested name doesn't exist: {name}"})
        resp.status_code = 404
        return resp

    db.session.delete(score)
    db.session.commit()

    resp = jsonify({'message': f"Successfully deleted: {name}"})
    resp.status_code = 200
    return resp


def download_dataset():
    global testdata
    if testdata is None:
        app.logger.info('download test data')
        testdata_url = os.environ.get('TESTDATA_URL')
        os.system(f'wget -q -O /tmp/test.csv {testdata_url}')
        testdata = pd.read_csv('/tmp/test.csv')


def init_competition():
    if db.session.query(Competition).count() == 0:
        default = Competition(name='Competition', disclose_private=False, )
        db.session.add(default)
        db.session.commit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
