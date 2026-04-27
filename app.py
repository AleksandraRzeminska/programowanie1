from flask import Flask, render_template, g, request, redirect, url_for, flash
import secrets
import sqlite3


app = Flask(__name__) 
app.config["SECRET_KEY"] = secrets.token_urlsafe(16)
DATABASE = "todo.db"
SCHEMA_SQL = """CREATE TABLE IF NOT EXISTS tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT NOT NULL, 
done INTEGER NOT NULL DEFAULT 0 CHECK (done in (0,1)),
created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
"""

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row 


        conn.execute("PRAGMA foreign_keys = ON; ")
        g.db = conn
    return g.db 

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()

@app.cli.command("init-db")
def init_db_command():
    init_db()
    print("Baza danych ToDo zostala zainicjalizowana.")


@app.cli.command("seed-db")
def seed_db():
    db = get_db()


    howManyRows = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    if howManyRows ==0:
        db.executemany("INSERT INTO tasks(title, done) VALUES (?, ?)",[["Iść po mleko", 0], ["Wygrać w kasynie", 0], ["Otworzyć cieśninę", 1]])
        db.commit()
        print("Dodano przykładowe dane")

    else:
        print("Tabela nie jest pusta, pomijam seed")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ping-db")
def ping_db():
    db = get_db()
    db.execute("SELECT 1").fetchone()
    return render_template("ping.html")

@app.route("/list")
def list():
    db = get_db()
    tasks = db.execute("SELECT id, title, done, created_at FROM tasks ORDER BY created_at DESC").fetchall()
    return render_template('list.html', tasks = tasks)

@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        title = request.form.get("title").strip()
        if len(title) < 4:
            error = f"Tytuł musi być dłuższy"
            return render_template('add_task.html', error = error )
        db = get_db()
        existingTask = db.execute("SELECT id FROM tasks WHERE title LIKE ? ", [title]).fetchone()
        if existingTask:
            error = f"Istnieje juz zadanie o tytule: {title}"
            return render_template('add_task.html', error = error )
        db.execute("INSERT INTO tasks(title, done) VALUES (?, ?)", (title, 0))
        db.commit()
        flash("Dodano zadanie")
        return redirect(url_for('list'))
    return render_template('add_task.html')

@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET done = NOT done WHERE id = ?", [task_id])
    db.commit()
    return redirect(url_for('list'))

@app.route("/tasks/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", [task_id])
    db.commit()
    flash("Usunięto zadanie")
    return redirect(url_for('list'))



if __name__ == "__main__":
    app.run(debug=True)
