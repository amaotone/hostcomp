# Hostcomp

Let's host a minimal data analysis competition.

## Features

- Automatic Scoring
- Public/Private Leaderboard

## Getting Started

1. [Create Heroku account](https://signup.heroku.com/) and [install Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).

2. Clone this repository.

```bash
$ git clone https://github.com/amaotone/hostcomp
$ cd hostcomp
```

3. Setup your heroku app.

```bash
$ heroku create <your-app-name>
$ heroku config:set TESTDATA_URL=<your-testdata-url>
$ heroku config:set ADMIN_PASSWORD=<your-admin-password>
$ heroku addons:create heroku-postgresql:hobby-dev
$ git push heroku master
```

4. Initialize your DB.

```bash
$ heroku run python
>>> from app import db, init_competition
>>> db.create_all()
>>> init_competition()
```

5. Access your website and update config.

## Author

Amane Suzuki <amane.suzu@gmail.com>
