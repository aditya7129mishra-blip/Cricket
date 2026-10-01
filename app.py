from pathlib import Path
import sqlite3

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE = Path(__file__).resolve().parent
DB = BASE / "bdpl.db"

app = FastAPI(title="BDPL Tournament Management System")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_db()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS tournament (
            id INTEGER PRIMARY KEY CHECK(id=1),
            name TEXT NOT NULL DEFAULT 'Bengal District Premier League',
            venue TEXT DEFAULT 'ASP Stadium',
            auction_date TEXT,
            start_date TEXT,
            end_date TEXT,
            prize_pool INTEGER DEFAULT 220000,
            organizer TEXT DEFAULT 'Nilanjan Panja & Shivam Bhajoriya',
            developer TEXT DEFAULT 'Aditya Mishra'
        );

        INSERT OR IGNORE INTO tournament(id) VALUES(1);

        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            district TEXT
        );

        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_date TEXT,
            match_time TEXT,
            team_a TEXT,
            team_b TEXT,
            venue TEXT,
            status TEXT DEFAULT 'Scheduled'
        );

        CREATE TABLE IF NOT EXISTS live_match (
            id INTEGER PRIMARY KEY CHECK(id=1),
            batting_team TEXT,
            bowling_team TEXT,
            striker TEXT,
            non_striker TEXT,
            bowler TEXT,
            runs INTEGER DEFAULT 0,
            wickets INTEGER DEFAULT 0,
            balls INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Not Started'
        );

        INSERT OR IGNORE INTO live_match(id) VALUES(1);

        CREATE TABLE IF NOT EXISTS awards (
            id INTEGER PRIMARY KEY CHECK(id=1),
            man_of_match TEXT,
            best_batsman TEXT,
            best_bowler TEXT,
            best_fielder TEXT,
            man_of_series TEXT,
            champion TEXT
        );

        INSERT OR IGNORE INTO awards(id) VALUES(1);
        """
    )
    con.commit()
    con.close()


init_db()


class Setup(BaseModel):
    name: str
    venue: str
    auction_date: str = ""
    start_date: str = ""
    end_date: str = ""
    prize_pool: int = 0


class Team(BaseModel):
    name: str
    district: str = ""


class Player(BaseModel):
    name: str


class Match(BaseModel):
    match_date: str
    match_time: str
    team_a: str
    team_b: str
    venue: str


class LiveSetup(BaseModel):
    batting_team: str
    bowling_team: str
    striker: str
    non_striker: str
    bowler: str


class Ball(BaseModel):
    event: str


class Awards(BaseModel):
    man_of_match: str = ""
    best_batsman: str = ""
    best_bowler: str = ""
    best_fielder: str = ""
    man_of_series: str = ""
    champion: str = ""


@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/api/all")
def get_all():
    con = get_db()
    tournament_row = con.execute(
        "SELECT * FROM tournament WHERE id=1"
    ).fetchone()
    tournament = dict(tournament_row)

    teams = []
    for team in con.execute("SELECT * FROM teams ORDER BY name"):
        team_data = dict(team)
        team_data["players"] = [
            dict(player)
            for player in con.execute(
                "SELECT id,name FROM players WHERE team_id=? ORDER BY name",
                (team["id"],),
            )
        ]
        teams.append(team_data)

    matches = [
        dict(row)
        for row in con.execute(
            "SELECT * FROM matches ORDER BY match_date,match_time"
        )
    ]
    live = dict(con.execute("SELECT * FROM live_match WHERE id=1").fetchone())
    awards = dict(con.execute("SELECT * FROM awards WHERE id=1").fetchone())
    con.close()

    return {
        "tournament": tournament,
        "teams": teams,
        "matches": matches,
        "live": live,
        "awards": awards,
    }


@app.post("/api/setup")
def setup(data: Setup):
    con = get_db()
    con.execute(
        """
        UPDATE tournament
        SET name=?, venue=?, auction_date=?, start_date=?, end_date=?, prize_pool=?
        WHERE id=1
        """,
        (
            data.name,
            data.venue,
            data.auction_date,
            data.start_date,
            data.end_date,
            max(0, data.prize_pool),
        ),
    )
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/teams")
def add_team(data: Team):
    con = get_db()
    try:
        cur = con.execute(
            "INSERT INTO teams(name,district) VALUES(?,?)",
            (data.name.strip(), data.district.strip()),
        )
        team_id = cur.lastrowid
        con.commit()
        return {"ok": True, "id": team_id}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "Team already exists."}
    finally:
        con.close()


@app.delete("/api/teams/{team_id}")
def delete_team(team_id: int):
    con = get_db()
    con.execute("DELETE FROM players WHERE team_id=?", (team_id,))
    con.execute("DELETE FROM teams WHERE id=?", (team_id,))
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/teams/{team_id}/players")
def add_player(team_id: int, data: Player):
    con = get_db()
    con.execute(
        "INSERT INTO players(team_id,name) VALUES(?,?)",
        (team_id, data.name.strip()),
    )
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/matches")
def add_match(data: Match):
    con = get_db()
    con.execute(
        """
        INSERT INTO matches(match_date,match_time,team_a,team_b,venue)
        VALUES(?,?,?,?,?)
        """,
        (data.match_date, data.match_time, data.team_a, data.team_b, data.venue),
    )
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/live/setup")
def setup_live(data: LiveSetup):
    con = get_db()
    con.execute(
        """
        UPDATE live_match
        SET batting_team=?, bowling_team=?, striker=?, non_striker=?, bowler=?,
            runs=0, wickets=0, balls=0, status='LIVE'
        WHERE id=1
        """,
        (
            data.batting_team,
            data.bowling_team,
            data.striker,
            data.non_striker,
            data.bowler,
        ),
    )
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/live/ball")
def score_ball(data: Ball):
    con = get_db()
    row = con.execute("SELECT * FROM live_match WHERE id=1").fetchone()
    runs = row["runs"]
    wickets = row["wickets"]
    balls = row["balls"]

    if data.event in ["wd", "nb"]:
        runs += 1
    elif data.event == "w":
        wickets += 1
        balls += 1
    else:
        runs += int(data.event)
        balls += 1

    con.execute(
        "UPDATE live_match SET runs=?, wickets=?, balls=?, status='LIVE' WHERE id=1",
        (runs, wickets, balls),
    )
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/live/reset")
def reset_live():
    con = get_db()
    con.execute(
        """
        UPDATE live_match
        SET runs=0, wickets=0, balls=0, status='Not Started'
        WHERE id=1
        """
    )
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/awards")
def save_awards(data: Awards):
    con = get_db()
    con.execute(
        """
        UPDATE awards
        SET man_of_match=?, best_batsman=?, best_bowler=?, best_fielder=?,
            man_of_series=?, champion=?
        WHERE id=1
        """,
        (
            data.man_of_match,
            data.best_batsman,
            data.best_bowler,
            data.best_fielder,
            data.man_of_series,
            data.champion,
        ),
    )
    con.commit()
    con.close()
    return {"ok": True}