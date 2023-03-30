import requests
from flask import Flask, render_template, request, flash, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, Form, SelectField
from wtforms.validators import InputRequired, Length, EqualTo, DataRequired
from wtforms.fields.html5 import EmailField
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import os
import sqlite3
from sqlite3 import Error
import time
import datetime
import arrow
from chart_studio import plotly as py
from plotly.graph_objs import *
from subprocess import call

currentlocation = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
'''
session = requests.Session()
session. = None
username = None
'''

login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, username, email, password, role):
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.authenticated = False


    def is_active(self):
        return self.is_active()

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return self.authenticated

    def is_active(self):
        return True

    def get_id(self):
        return self.username

    def get_role(self):
        return self.role


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


class RegistrationForm(Form):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "User Name"})
    firstname = StringField('firstname', validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "First Name"})
    lastname = StringField('lastname', validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Last Name"})
    emailaddress = EmailField('email', validators=[DataRequired(), EqualTo('retype_emailaddress',
                                                                           message='Email must match')],
                              render_kw={"placeholder": "Email Address"})
    retype_emailaddress = EmailField('retypeemail', validators=[DataRequired()], render_kw={"placeholder": "Retype Email Address"})
    password = PasswordField('password', validators=[DataRequired(), Length(min=6, max=20), EqualTo('retype_password',
                                                                                                    message='Password missmatched, need to be similar')], render_kw={"placeholder": "Password"})
    retype_password = PasswordField('Retypepassword', validators=[DataRequired(), Length(min=6, max=20)], render_kw={"placeholder": "Retype Password"})


class LoginForm(Form):
    username = StringField('username', validators=[InputRequired(),
                                                   Length(min=4, max=20)], render_kw={"placeholder": "User Name"})
    emailaddress = EmailField('email', validators=[DataRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Email Address"})
    password = PasswordField('password', validators=[DataRequired(), Length(min=6, max=20)], render_kw={"placeholder": "Password"})


class AdminForm(Form):
    conn = create_connection(os.path.join(currentlocation, 'userdb.db'))
    curs = conn.cursor()
    curs.execute("SELECT USERNAME, EMAIL FROM USERS")
    lu = curs.fetchall()
    userlist=[]
    emaillist=[]
    accesslist = ['admin', 'white_list', 'black_list']
    for username, email in lu:
        userlist.append(username)
        emaillist.append(email)

    username_list = SelectField('username_list', choices=userlist)
    emailaddress_list = SelectField('emailaddress_list', choices=emaillist)
    access_list = SelectField('access_list', choices=accesslist)


@login_manager.user_loader
def load_user(user_id):
   conn = create_connection(os.path.join(currentlocation, 'userdb.db'))
   curs = conn.cursor()
   curs.execute("SELECT USERNAME, EMAIL, PASSWORD, ROLE FROM USERS where USERNAME=?", (user_id,))
   lu = curs.fetchone()
   if lu is None:
      return None
   else:
      return User(lu[0], lu[1], lu[2], lu[3])


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('lab_env_db'))

    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        conn = create_connection(os.path.join(currentlocation, 'userdb.db'))
        c = conn.cursor()
        c.execute("SELECT USERNAME, EMAIL, PASSWORD, ROLE FROM USERS where USERNAME=?", (request.form['username'],))
        check_username = c.fetchone()
        if check_username is not None:
            entry = list(check_username)
            user = load_user(entry[0])
            print(user)
            if request.form['emailaddress'] == user.email:
                if check_password_hash(password=request.form['password'], pwhash=user.password):
                    login_user(user)
                    if user.role == 'black_list':
                        return "You are blocked: You do not have access to the system"
                    return redirect(url_for('lab_env_db'))
                else:
                    flash("Wrong password .. please check", "info")
            else:
                flash("Your emailaddress hasn't registered.. Please register to the system", "info")
        else:
            flash("Your Username hasn't registered.. Have you registered to the system? Please register", "info")
    return render_template("login.html", form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        username = request.form['username']
        email_address = request.form['emailaddress']
        conn = create_connection(os.path.join(currentlocation, 'userdb.db'))
        c = conn.cursor()
        c.execute("SELECT USERNAME FROM USERS where USERNAME=?", (username,))
        check_username = c.fetchone()

        c.execute("SELECT EMAIL FROM USERS where EMAIL=?", (email_address,))
        check_email = c.fetchone()

        if check_username is not None:
            flash("Your username has already taken.. Choose a new one or try to Log in", "info")
            return render_template("signup.html", form=form)
        elif check_email is not None:
            flash("Your email has already Registered.. Choose a new one or try to Log in", "info")
            return render_template("signup.html", form=form)
        else:
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            emailaddress = request.form['emailaddress']
            password = generate_password_hash(request.form['password'])
            c.execute("INSERT INTO USERS VALUES(?,?,?,?,?,?)", (username, firstname, lastname, emailaddress, password, 'white_list'))
            ''' Primarily every user will be considered as white_list '''
            conn.commit()
            form = LoginForm()
            return render_template('login.html', form=form)
    return render_template("signup.html", form=form)


@app.route("/admin", methods=['GET', 'POST'])
def admin():
    form = AdminForm(request.form)
    if not current_user.is_authenticated:
        flash("You are not logged in.. try to log in first", "info")
        return render_template("login.html", form=LoginForm())
    if not current_user.get_role() == 'admin':
        flash("You are not admin.. You don't have access to admin page", "info")
        return render_template("login.html", form=LoginForm())

    if request.method == "POST" and form.validate():
        username = form.username_list.data
        emailaddress = form.emailaddress_list.data
        access = form.access_list.data

        conn = create_connection(os.path.join(currentlocation, 'userdb.db'))
        c = conn.cursor()
        c.execute("UPDATE USERS SET ROLE=? WHERE USERNAME=? AND EMAIL=?", (access, username, emailaddress))
        conn.commit()
        flash("Your user access is updated perfectly", "info")
    return render_template("admin.html", form=form)


@app.route("/lab_env_db", methods=['GET', 'POST'])  # Add date limits in the URL #Arguments: from=2015-03-04&to=2015-03-05
def lab_env_db():
    '''
    global username
    if username not in session:
        return render_template(url_for("login.html"))
    '''

    if not current_user.is_authenticated:
        flash("You are not logged in.. try to log in first", "info")
        return render_template("login.html", form=LoginForm())

    temperatures, humidities, timezone, from_date_str, to_date_str = get_records()

    # Create new record tables so that datetimes are adjusted back to the user browser's time zone.
    time_adjusted_temperatures = []
    time_adjusted_humidities = []
    for record in temperatures:
        local_timedate = arrow.get(record[0][:len(record[0]) - 3], "YYYY-MM-DD HH:mm").to(timezone)
        time_adjusted_temperatures.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2], 2)])

    for record in humidities:
        local_timedate = arrow.get(record[0][:len(record[0]) - 3], "YYYY-MM-DD HH:mm").to(timezone)
        time_adjusted_humidities.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2], 2)])

    print("rendering lab_env_db.html with: %s, %s, %s" % (timezone, from_date_str, to_date_str))

    return render_template("lab_env_db.html", timezone	= timezone,
                           temp 			= time_adjusted_temperatures,
                           hum 			= time_adjusted_humidities,
                           from_date 		= from_date_str,
                           to_date 		= to_date_str,
                           temp_items 		= len(temperatures),
                           query_string	= request.query_string,  # This query string is used
                           # by the Plotly link
                           hum_items 		= len(humidities))


def get_records():
    from_date_str 	= request.args.get('from' ,time.strftime("%Y-%m-%d 00:00"))  # Get the from date value from the URL
    to_date_str 	= request.args.get('to' ,time.strftime("%Y-%m-%d %H:%M"))  # Get the to date value from the URL
    timezone 		= request.args.get('timezone' ,'Etc/UTC');
    range_h_form	= request.args.get('range_h' ,'');  # This will return a string, if field range_h exists in the request
    range_h_int 	= "nan"  # initialise this variable with not a number

    print( "REQUEST:")
    print( request.args)

    try:
        range_h_int	= int(range_h_form)
    except:
        print( "range_h_form not a number")


    print( "Received from browser: %s, %s, %s, %s" % (from_date_str, to_date_str, timezone, range_h_int))

    if not validate_date(from_date_str):			# Validate date before sending it to the DB
        from_date_str 	= time.strftime("%Y-%m-%d 00:00")
    if not validate_date(to_date_str):
        to_date_str 	= time.strftime("%Y-%m-%d %H:%M")		# Validate date before sending it to the DB
    print( '2. From: %s, to: %s, timezone: %s' % (from_date_str ,to_date_str ,timezone))
    # Create datetime object so that we can convert to UTC from the browser's local time
    from_date_obj       = datetime.datetime.strptime(from_date_str ,'%Y-%m-%d %H:%M')
    to_date_obj         = datetime.datetime.strptime(to_date_str ,'%Y-%m-%d %H:%M')

    # If range_h is defined, we don't need the from and to times
    if isinstance(range_h_int ,int):
        # arrow_time_from = arrow.utcnow().replace(hours=-range_h_int)
        arrow_time_from = arrow.utcnow().shift(hours=-range_h_int) # EST TIME
        arrow_time_to   = arrow.utcnow()
        from_date_utc   = arrow_time_from.strftime("%Y-%m-%d %H:%M")
        to_date_utc     = arrow_time_to.strftime("%Y-%m-%d %H:%M")
        from_date_str   = arrow_time_from.to(timezone).strftime("%Y-%m-%d %H:%M")
        to_date_str	    = arrow_time_to.to(timezone).strftime("%Y-%m-%d %H:%M")
    else:
        # Convert datetimes to UTC so we can retrieve the appropriate records from the database
        from_date_utc   = arrow.get(from_date_obj, timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")
        to_date_utc     = arrow.get(to_date_obj, timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")

    # conn 			    = sqlite3.connect('/var/www/lab_app/lab_app.db')
    conn = sqlite3.connect(os.path.join(currentlocation, 'lab_app.db'))
    curs 			    = conn.cursor()
    curs.execute("SELECT * FROM temperatures WHERE rDateTime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
    temperatures 	    = curs.fetchall()
    curs.execute("SELECT * FROM humidities WHERE rDateTime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
    humidities 		    = curs.fetchall()
    conn.close()

    return [temperatures, humidities, timezone, from_date_str, to_date_str]


@app.route("/to_plotly", methods=['GET'])  # This method will send the data to ploty.
def to_plotly():
    '''  code for session assigning     '''
    if not current_user.is_authenticated:
        flash("You are not logged in.. try to log in first", "info")
        return render_template("login.html", form=LoginForm())

    temperatures, humidities, timezone, from_date_str, to_date_str = get_records()

    # Create new record tables so that datetimes are adjusted back to the user browser's time zone.
    time_series_adjusted_tempreratures  = []
    time_series_adjusted_humidities 	= []
    time_series_temprerature_values 	= []
    time_series_humidity_values 		= []

    for record in temperatures:
        local_timedate = arrow.get(record[0][:len(record[0]) - 3], "YYYY-MM-DD HH:mm").to(timezone)
        time_series_adjusted_tempreratures.append(local_timedate.format('YYYY-MM-DD HH:mm'))
        time_series_temprerature_values.append(round(record[2] ,2))

    for record in humidities:
        local_timedate = arrow.get(record[0][:len(record[0]) - 3], "YYYY-MM-DD HH:mm").to(timezone)
        time_series_adjusted_humidities.append \
            (local_timedate.format('YYYY-MM-DD HH:mm'))  # Best to pass datetime in text
        # so that Plotly respects it
        time_series_humidity_values.append(round(record[2] ,2))

    temp = Scatter(
        x=time_series_adjusted_tempreratures,
        y=time_series_temprerature_values,
        name='Temperature'
    )
    hum = Scatter(
        x=time_series_adjusted_humidities,
        y=time_series_humidity_values,
        name='Humidity',
        yaxis='y2'
    )

    data = Data([temp, hum])

    layout = Layout(
        title="Temperature and Humidity in Clayton's Apartment",
        xaxis=XAxis(
            type='date',
            autorange=True
        ),
        yaxis=YAxis(
            title='Fahrenheit',
            type='linear',
            autorange=True
        ),
        yaxis2=YAxis(
            title='Percent',
            type='linear',
            autorange=True,
            overlaying='y',
            side='right'
        )

    )
    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='lab_temp_hum')

    return plot_url


def validate_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=8082)