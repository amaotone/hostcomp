import logging
import os
import sqlite3

import pandas as pd
from flask import Flask, g, jsonify, make_response, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sklearn.metrics import mean_absolute_error

app = Flask(__name__)
db_uri = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(app.root_path, 'hostcomp.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)

testdata = None


class Score(db.Model):
    __tablename__ = 'scores'
    name = db.Column(db.String(), primary_key=True)
    public = db.Column(db.Float, nullable=False)
    private = db.Column(db.Float, nullable=False)


@app.route('/')
def index():
    scores = Score.query.all()
    scores = sorted(scores, key=lambda x: x.public)
    return render_template('index.html', scores=scores, title='public leaderboard', private=False)


@app.route('/private')
def private():
    scores = Score.query.all()
    scores = sorted(scores, key=lambda x: x.private)
    return render_template('index.html', scores=scores, title='private leaderboard', private=True)


@app.route('/submit', methods=['POST'])
def submit():
    download_dataset()
    if request.headers['Content-Type'] != 'application/json':
        app.logger.info(request.headers['Content-Type'])
        return jsonify({'error': f'Invalid Content-Type: {request.headers["Content-Type"]}'})
    data = request.json

    if 'name' not in data:
        return jsonnify({'error': 'You must specify the name.'})
    name = data['name']
    pred = list(map(float, data['pred']))

    if len(pred) != len(testdata):
        return jsonify({'error': f'Invalid pred length: {len(pred)}. len(pred) must be {len(testdata)}'})

    testdata['pred'] = pred
    public_score = mean_absolute_error(testdata['target'], testdata['pred'], (testdata['private'] == 0).astype(float))
    private_score = mean_absolute_error(testdata['target'], testdata['pred'], (testdata['private'] == 1).astype(float))

    score = Score()
    score.name = name
    score.public = public_score
    score.private = private_score
    db.session.merge(score)
    db.session.commit()
    return jsonify({'name': name, 'public_score': public_score})


@app.route('/delete', methods=['POST'])
def delete():
    if request.headers['Content-Type'] != 'application/json':
        app.logger.info(request.headers['Content-Type'])
        return jsonify({'error': f'Invalid Content-Type: {request.headers["Content-Type"]}'})
    data = request.json

    if 'name' not in data:
        return jsonify({'error': 'You must specify the name.'})
    name = data['name']

    score = Score.query.filter_by(name=name).first()
    if not score:
        return jsonify({'error': f"Doesn't exist: {name}"})
    db.session.delete(score)
    db.session.commit()
    return jsonify({'message': f"Successfully deleted: {name}"})


def download_dataset():
    global testdata
    if testdata is None:
        app.logger.info('download test data')
        testdata_url = os.environ.get('TESTDATA_URL')
        os.system(f'wget -q -O /tmp/test.csv {testdata_url}')
        testdata = pd.read_csv('/tmp/test.csv')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
