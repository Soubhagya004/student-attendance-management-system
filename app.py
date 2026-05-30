from flask import Flask, render_template, request, redirect, url_for, session
from datetime import date
import mysql.connector

app = Flask(__name__)
app.secret_key = "attendance_secret_key"

# ---------------- DATABASE ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Addi@123",
    database="attendance_db"
)

cursor = db.cursor()

# ---------------- ALWAYS START HERE ----------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("""
            SELECT * FROM users 
            WHERE username=%s AND password=%s
        """, (username, password))

        user = cursor.fetchone()

        if user:
            session['user'] = user[1]
            session['role'] = user[3]

            if user[3] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            
            else:
                return redirect(url_for('teacher_dashboard'))

        

        return render_template("login.html",
                       error="Invalid Username or Password")

    return render_template("login.html")

#------------ forgot password -------------

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- DASHBOARDS ----------------
@app.route('/admin')
def admin_dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Admin':
        return "Access Denied ❌"

    return render_template("admin_dashboard.html")


@app.route('/teacher')
def teacher_dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Teacher':
        return "Access Denied ❌"

    return render_template("teacher_dashboard.html")


# ---------------- STUDENTS ----------------
@app.route('/students', methods=['GET', 'POST'])
def students():

    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        usn = request.form['usn']
        department = request.form['department']

        cursor.execute("""
            INSERT INTO students(name, usn, department)
            VALUES (%s, %s, %s)
        """, (name, usn, department))

        db.commit()
        return redirect(url_for('view_students'))

    return render_template("students.html")


# ---------------- VIEW ----------------
@app.route('/view')
def view_students():

    if 'user' not in session:
        return redirect(url_for('login'))

    # Sort students by USN
    cursor.execute("""
        SELECT * FROM students
        ORDER BY usn ASC
    """)

    data = cursor.fetchall()

    return render_template("view.html", students=data)

# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete_student(id):

    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    db.commit()

    return redirect(url_for('view_students'))


# ---------------- EDIT ----------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):

    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        usn = request.form['usn']
        department = request.form['department']

        cursor.execute("""
            UPDATE students 
            SET name=%s, usn=%s, department=%s 
            WHERE id=%s
        """, (name, usn, department, id))

        db.commit()
        return redirect(url_for('view_students'))

    cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cursor.fetchone()

    return render_template("edit.html", student=student)


# ---------------- ATTENDANCE ----------------
@app.route('/mark/<int:id>/<status>')
def mark_attendance(id, status):

    if 'user' not in session:
        return redirect(url_for('login'))

    today = date.today()

    cursor.execute("""
        INSERT INTO attendance(student_id, date, status)
        VALUES (%s, %s, %s)
    """, (id, today, status))

    db.commit()
    return redirect(url_for('view_students'))


# ---------------- ATTENDANCE REPORT ----------------
@app.route('/attendance')
def attendance_report():

    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("""
        SELECT s.name, s.usn, a.date, a.status
        FROM students s
        JOIN attendance a ON s.id = a.student_id
    """)

    data = cursor.fetchall()

    return render_template("attendance.html", data=data)


# ---------------- ANALYTICS ----------------
@app.route('/analytics')
def analytics():

    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
    present = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE status='Absent'")
    absent = cursor.fetchone()[0]

    return render_template("attendance_report.html",
                           present=present,
                           absent=absent)


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()