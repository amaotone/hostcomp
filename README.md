# Hostcomp

Let's host a minimal data analysis competition.

## Features

- Automatic Scoring
- Public/Private Leaderboard

## Getting Started

1. Clone this repository.

```bash
$ git clone https://github.com/amaotone/hostcomp
$ cd hostcomp
```

2. Setup your heroku app.

```bash
$ heroku create <your-app-name>
$ heroku config:set TESTDATA_URL=<your-testdata-url>
$ heroku config:set COMPETITION_NAME=<your-competition-name>
$ heroku addons:create heroku-postgresql:hobby-dev
$ git push heroku master
```

3. Initialize your DB.

```bash
$ heroku run python
>>> from app import db
>>> db.create_all()
```

## Author

Amane Suzuki
