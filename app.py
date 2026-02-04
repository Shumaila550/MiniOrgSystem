from flask import Flask, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey"

def get_db():
    return sqlite3.connect("organization.db")

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        date TEXT,
        status TEXT
    )
    """)

    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users VALUES (NULL,?,?,?)",
            ("admin", generate_password_hash("admin123"), "admin")
        )

    db.commit()
    db.close()

init_db()

@app.route("/", methods=["GET","POST"])
def login():
    msg=""
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]

        db=get_db()
        c=db.cursor()
        c.execute("SELECT password,role FROM users WHERE username=?", (u,))
        user=c.fetchone()
        db.close()

        if user and check_password_hash(user[0],p):
            session["user"]=u
            session["role"]=user[1]
            return redirect("/dashboard")
        else:
            msg="Invalid login"

    return f"""
    <h2>Login</h2>
    <p style='color:red'>{msg}</p>
    <form method='post'>
    <input name='username' placeholder='Username' required><br><br>
    <input type='password' name='password' placeholder='Password' required><br><br>
    <button>Login</button>
    </form>
    <a href='/register'>Register</a>
    """

@app.route("/register", methods=["GET","POST"])
def register():
    msg=""
    if request.method=="POST":
        u=request.form["username"]
        p=generate_password_hash(request.form["password"])

        try:
            db=get_db()
            c=db.cursor()
            c.execute("INSERT INTO users VALUES (NULL,?,?,?)",(u,p,"user"))
            db.commit()
            db.close()
            return redirect("/")
        except:
            msg="User exists"

    return f"""
    <h2>Register</h2>
    <p style='color:red'>{msg}</p>
    <form method='post'>
    <input name='username' required><br><br>
    <input type='password' name='password' required><br><br>
    <button>Register</button>
    </form>
    <a href='/'>Login</a>
    """

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    admin=""
    if session["role"]=="admin":
        admin="<a href='/admin'>Admin Panel</a><br>"

    return f"""
    <h2>Dashboard</h2>
    <p>Welcome {session['user']}</p>
    <a href='/attendance'>Attendance</a><br>
    {admin}
    <a href='/logout'>Logout</a>
    """

@app.route("/attendance", methods=["GET","POST"])
def attendance():
    if "user" not in session:
        return redirect("/")

    db=get_db()
    c=db.cursor()

    if request.method=="POST":
        c.execute(
            "INSERT INTO attendance VALUES (NULL,?,?,?)",
            (session["user"], request.form["date"], request.form["status"])
        )
        db.commit()

    c.execute("SELECT date,status FROM attendance WHERE username=?", (session["user"],))
    rows="".join(f"<tr><td>{r[0]}</td><td>{r[1]}</td></tr>" for r in c.fetchall())
    db.close()

    return f"""
    <h2>Attendance</h2>
    <form method='post'>
    <input type='date' name='date' required>
    <select name='status'><option>Present</option><option>Absent</option></select>
    <button>Add</button>
    </form>
    <table border='1'><tr><th>Date</th><th>Status</th></tr>{rows}</table>
    <a href='/dashboard'>Back</a>
    """

@app.route("/admin")
def admin():
    if "role" not in session or session["role"]!="admin":
        return redirect("/dashboard")

    db=get_db()
    c=db.cursor()
    c.execute("SELECT username,role FROM users")
    users=c.fetchall()
    c.execute("SELECT username,date,status FROM attendance")
    att=c.fetchall()
    db.close()

    urows="".join(f"<tr><td>{u[0]}</td><td>{u[1]}</td></tr>" for u in users)
    arows="".join(f"<tr><td>{a[0]}</td><td>{a[1]}</td><td>{a[2]}</td></tr>" for a in att)

    return f"""
    <h2>Admin Panel</h2>
    <h3>Users</h3>
    <table border='1'>{urows}</table>
    <h3>Attendance</h3>
    <table border='1'>{arows}</table>
    <a href='/dashboard'>Back</a>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
