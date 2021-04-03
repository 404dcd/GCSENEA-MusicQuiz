DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS game;
DROP TABLE IF EXISTS songs;
DROP TABLE IF EXISTS cookies;

CREATE TABLE users (
    userid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    passwd TEXT NOT NULL,
    isadmin BOOLEAN
);

CREATE TABLE game (
    userid INTEGER PRIMARY KEY,
    display TEXT NOT NULL,
    currscore INTEGER NOT NULL,
    currsong INTEGER NOT NULL,
    attempts INTEGER NOT NULL,
    used TEXT NOT NULL,
    highscore INTEGER NOT NULL
);

CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist TEXT NOT NULL,
    title TEXT NOT NULL
);

CREATE TABLE cookies (
    sessionid TEXT UNIQUE NOT NULL,
    userid INTEGER UNIQUE NOT NULL,
    expiration INTEGER NOT NULL
);

INSERT INTO songs (artist, title) VALUES ("Test Artist 1", "Foo Bar");
INSERT INTO songs (artist, title) VALUES ("Test Artist 2", "This Is A Test Song");
INSERT INTO songs (artist, title) VALUES ("Test Artist 3", "One Two Three");