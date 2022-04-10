from flask import Flask, redirect, render_template, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import null
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3' 
app.secret_key = 'secret_key'
app.config['SESSION_TYPE'] = "filesystem"
db = SQLAlchemy(app)

class Tracker(db.Model):
    __tablename__ = 'Tracker'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tname = db.Column(db.String)
    tdesc = db.Column(db.String)
    ttype = db.Column(db.String)
    multi_select = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))                  #//TODO - Adding datetime obj
    tdata = db.relationship('TrackerData', backref="tracker")

class Users(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fname = db.Column(db.String)
    lname = db.Column(db.String)
    email = db.Column(db.String)
    username = db.Column(db.String, unique=True, nullable=False)            #//TODO - Hashing Password
    password = db.Column(db.String, nullable=False)
    trackers = db.relationship('Tracker', backref="user")

class TrackerData(db.Model):
    __tablename__ = 'TrackerData'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tracker_id = db.Column(db.Integer, db.ForeignKey('Tracker.id'))
    date = db.Column(db.String, nullable=False)
    value = db.Column(db.Integer, nullable=True)
    rad_value = db.Column(db.String, nullable=True)
    notes = db.Column(db.String, nullable=False)
    

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        flag = False

        if username!="" and password!="":
            existing_users = Users.query.all()
            for user in existing_users:
                if user.username == username and user.password == password:
                    flag = False
                    session['user'] = username
                    return redirect(url_for('dashboard', username = username))  

                else:
                    flag = True
        if flag == True:
            msg = "Invalid Credentials"
            return render_template('login.html', flag = flag, msg = msg)                                 
        
        else:
            return redirect('/')                                                #// TODO -error message pop-up needed and remove redirection    

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    if request.method == 'POST':

        fname = request.form['fname']
        lname = request.form['lname']
        username = request.form['username']
        email = request.form['email']                                       #//TODO - email validation
        password = request.form['password']                                 #//TODO - password validation
        confirm_password = request.form['confirm_password'] 

        if password != confirm_password:
            return redirect('/')                                            #//FIXME - Change redirect page

        else:
            flag = False
            existing_users = Users.query.all()
            for user in existing_users:
                if username == user.username:
                    flag = True
            if flag:
                return redirect('register')                                  #//FIXME - change error message [username already exists]
            else:
                user = Users(fname=fname, lname=lname, username=username, email=email, password=password)
                db.session.add(user)
                db.session.commit()
            return redirect('login')                                            #//FIXME - Display Successfully Account Created Message
        
@app.route('/logout')
def logout():
    session['user'] = None
    return redirect('/')

@app.route('/dashboard/<username>', methods = ['GET', 'POST'])
def dashboard(username):
    curr_user = session.get('user')
    curr_user_obj = db.session.query(Users).filter(Users.username==curr_user).first()
    curr_user_id = curr_user_obj.id
    curr_user_tdata = db.session.query(Tracker).filter(Tracker.user_id==curr_user_id).all()
    flag = False
    if curr_user_tdata == []:
        flag=True
    return render_template('user.html', username = username, tdata = curr_user_tdata, flag = flag)

@app.route('/addtracker', methods=['GET', 'POST'])
def addtracker():
    if request.method == 'GET':
        return render_template('new_tracker.html', username=session.get('user'))
    
    if request.method == 'POST':
        tracker_name = request.form['tname']                                            #//FIXME - accept only one word
        desc = request.form['description']
        ttype = request.form.getlist('type')[0]
        curr_user = session.get('user')
        curr_user_obj = db.session.query(Users).filter(Users.username==curr_user).first()
        curr_user_id = curr_user_obj.id
        if ttype == '1':
            tracker = Tracker(tname=tracker_name, tdesc=desc, ttype="integer", user_id=curr_user_id)
            db.session.add(tracker)
            db.session.commit()

        if ttype == '2':
            multi_select_values = request.form['settings']
            tracker = Tracker(tname=tracker_name, tdesc=desc, ttype="multiselect", multi_select=multi_select_values, user_id=curr_user_id)
            db.session.add(tracker)
            db.session.commit()
        

        return redirect("dashboard/{curr_user}".format(curr_user=curr_user))

@app.route('/dashboard/<username>/<int:id>')
def view_tracker(username, id):
    tracker_data = db.session.query(TrackerData).filter(TrackerData.tracker_id==id).all()
    t_name = db.session.query(Tracker).filter(Tracker.id==id).first()

    if t_name.ttype == "integer":
        flag = False
        log_value = []
        log_date = []
        for logs in tracker_data:
            log_value.append(logs.value)
            log_date.append(logs.date)
        plt.plot(log_date, log_value, marker='o', markerfacecolor='red', markersize=9, linestyle='--')
        plt.savefig('static/plt.png')
        plt.close()
        return render_template('tracker_info.html', username=session.get('user'), tracker_data=tracker_data, tname=t_name.tname, flag=flag)
    elif t_name.ttype == "multiselect":
        flag = True
        log_value = []
        log_date = []
        for logs in tracker_data:
            log_value.append(logs.rad_value)
            log_date.append(logs.date)
        plt.plot(log_date, log_value, marker='o', markerfacecolor='red', markersize=9)
        plt.savefig('static/plt.png')
        plt.close()
        return render_template('tracker_info.html', username=session.get('user'), tracker_data=tracker_data, tname=t_name.tname, flag=flag)

@app.route('/dashboard/<username>/<int:tid>/<int:lid>/delete')
def deleteLog(username, tid, lid):
    deletable = TrackerData.query.filter(TrackerData.tracker_id == tid and TrackerData.id == lid).first()
    db.session.delete(deletable)
    db.session.commit()
    return redirect('/dashboard/{0}/{1}'.format(username,tid))

@app.route('/dashboard/<username>/<int:tid>/<int:lid>/edit', methods=['POST', 'GET'])
def editLog(username, tid, lid):
    if request.method == 'GET':
        flag = False
        user_obj = db.session.query(Users).filter(Users.username == username).first()
        user_obj_id = user_obj.id
        user_trackers = db.session.query(Tracker).filter(Tracker.user_id == user_obj_id).all()
        for tracker in user_trackers:
            if tracker.id == tid:
                curr_tracker = tracker
        if curr_tracker.multi_select != None:
            flag = True
        vals = curr_tracker.multi_select
        split_strip_values = []
        if vals != None:
            split_values = vals.split(',')
            for val in split_values:
                split_strip_values.append(val.strip())
        tracker_log = TrackerData.query.filter(TrackerData.id == lid).first()

        return render_template('edit_log.html', user=session.get('user'), values = split_strip_values, flag = flag, username=session.get('user'), tracker=tracker_log)

    if request.method == 'POST':
        user_obj = db.session.query(Users).filter(Users.username == username).first()
        user_obj_id = user_obj.id
        user_trackers = db.session.query(Tracker).filter(Tracker.user_id == user_obj_id).all()
        for tracker in user_trackers:
            if tracker.id == tid:
                curr_tracker = tracker
        if curr_tracker.multi_select != None:
            radio_values = request.form['value']
            date = request.form['date']
            notes = request.form['notes']
            curr_log_ms = db.session.query(TrackerData).filter(TrackerData.id == lid).first()
            curr_log_ms.rad_value = radio_values
            curr_log_ms.date = date
            curr_log_ms.notes = notes
            db.session.commit()
        else:
            value = request.form['value']
            date = request.form['date']
            notes = request.form['notes']
            curr_log = db.session.query(TrackerData).filter(TrackerData.id == lid).first()
            curr_log.date = date
            curr_log.notes = notes
            curr_log.value = value
            db.session.commit()
        return redirect('/dashboard/{user}/{tid}'.format(user=session.get('user'), tid=curr_tracker.id))

@app.route('/dashboard/<username>/<int:tid>/delete')
def delTracker(username, tid):
    deletable = db.session.query(Tracker).filter(Tracker.id==tid).first()
    db.session.delete(deletable)
    db.session.commit()
    return redirect('/dashboard/{user}'.format(user=username))

@app.route('/dashboard/<username>/<int:tid>/edit', methods=['POST', 'GET'])
def editTracker(username, tid):
    if request.method == 'GET':
        curr_tracker = db.session.query(Tracker).filter(Tracker.id == tid).first()
        return render_template('edit_tracker.html', username=session.get('user'), tracker=curr_tracker)
    
    if request.method == 'POST':
        tracker_name = request.form['tname']                                            #//FIXME - accept only one word
        desc = request.form['description']
        curr_tracker = db.session.query(Tracker).filter(Tracker.id == tid).first()
        ttype = curr_tracker.ttype
        curr_user = session.get('user')
        curr_user_obj = db.session.query(Users).filter(Users.username==curr_user).first()
        curr_user_id = curr_user_obj.id
        if ttype == 'integer':
            curr_tracker.tname = tracker_name
            curr_tracker.tdesc = desc
            db.session.commit()

        if ttype == 'multiselect':
            multi_select_values = request.form['settings']
            curr_tracker.tname = tracker_name
            curr_tracker.tdesc = desc
            curr_tracker.multi_select = multi_select_values
            db.session.commit()
        

        return redirect("/dashboard/{curr_user}".format(curr_user=curr_user))

@app.route('/dashboard/<username>/logdata/<int:id>',  methods=['GET', 'POST'])
def logging(username, id):
    if request.method == 'GET':
        flag = False
        user_obj = db.session.query(Users).filter(Users.username == username).first()
        user_obj_id = user_obj.id
        user_trackers = db.session.query(Tracker).filter(Tracker.user_id == user_obj_id).all()
        for tracker in user_trackers:
            if tracker.id == id:
                curr_tracker = tracker
        if curr_tracker.multi_select != None:
            flag = True
        vals = curr_tracker.multi_select
        split_strip_values = []
        if vals != None:
            split_values = vals.split(',')
            for val in split_values:
                split_strip_values.append(val.strip())
            
        return render_template('log_tracker.html', user=session.get('user'), values = split_strip_values, flag = flag, username=session.get('user'))

    
    if request.method == 'POST':
        user_obj = db.session.query(Users).filter(Users.username == username).first()
        user_obj_id = user_obj.id
        user_trackers = db.session.query(Tracker).filter(Tracker.user_id == user_obj_id).all()
        for tracker in user_trackers:
            if tracker.id == id:
                curr_tracker = tracker
        if curr_tracker.multi_select != None:
            radio_values = request.form['value']
            date = request.form['date']
            notes = request.form['notes']
            tdata = TrackerData(tracker_id=id,date=date,rad_value=radio_values,notes=notes)
            db.session.add(tdata)
            db.session.commit()
        else:
            value = request.form['value']
            date = request.form['date']
            notes = request.form['notes']
            tdata = TrackerData(tracker_id=id,date=date,value=value,notes=notes)
            db.session.add(tdata)
            db.session.commit()

        return redirect('/dashboard/{user}/{tid}'.format(user=session.get('user'), tid=curr_tracker.id))



if __name__ == '__main__':
    app.run(debug=True)                                                    #//TODO - Remove debug mode during production