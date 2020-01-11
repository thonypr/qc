CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    task TEXT NOT NULL,
    answer_pattern TEXT NOT NULL,
    done TEXT NOT NULL,
    start_time TEXT NOT NULL
);