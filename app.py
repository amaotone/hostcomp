import logging
import os
import sqlite3

import pandas as pd
from flask import Flask, g, jsonify, make_response, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sklearn import metrics

app = Flask(__name__)
db_uri = os.environ.get('DATABASE_URL') or 'postgresql://localhost/hostcomp'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)

testdata = None
scoring_func = metrics.mean_absolute_error


class Score(db.Model):
    __tablename__ = 'scores'
    name = db.Column(db.String(), primary_key=True)
    public = db.Column(db.Float, nullable=False)
    private = db.Column(db.Float, nullable=False)


@app.route('/')
def index():
    scores = Score.query.all()
    scores = sorted(scores, key=lambda x: x.public)
    return render_template('index.html', scores=scores, title='public LB', private=False)


@app.route('/private')
def private():
    scores = Score.query.all()
    scores = sorted(scores, key=lambda x: x.private)
    return render_template('index.html', scores=scores, title='private LB', private=True)


@app.route('/submit', methods=['POST'])
def submit():
    download_dataset()
    if request.headers['Content-Type'] != 'application/json':
        app.logger.info(request.headers['Content-Type'])
        return jsonify({'error': f'Invalid Content-Type: {request.headers["Content-Type"]}'})
    data = request.json
    name = data['name']
    pred = list(map(float, data['pred']))

    if len(pred) != len(testdata):
        return jsonify({'error': f'Invalid pred length: {len(pred)}. len(pred) must be {len(testdata)}'})

    testdata['pred'] = pred
    public = testdata.query("not private")
    public_score = scoring_func(public['target'], public['pred'])
    private = testdata.query("private")
    private_score = scoring_func(private['target'], private['pred'])

    score = Score()
    score.name = name
    score.public = public_score
    score.private = private_score
    db.session.merge(score)
    db.session.commit()
    return jsonify({'name': name, 'public_score': public_score})


def download_dataset():
    global testdata
    if testdata is None:
        app.logger.info('download test data')
        testdata_url = os.environ.get('TESTDATA_URL')
        os.system(f'wget -q -O /tmp/test.csv {testdata_url}')
        testdata = pd.read_csv('/tmp/test.csv')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
