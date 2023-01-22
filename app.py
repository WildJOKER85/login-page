from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_security import RoleMixin
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, validators, EmailField, BooleanField
from werkzeug.security import generate_password_hash, check_password_hash

from config import DevEnvConfig
from constants import ErrorMessages as em, any_of_in_password
from helpers import generate_hash

app = Flask(__name__)
app.config.from_object(DevEnvConfig)
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


# csrf = CSRFProtect(app)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    roles = db.relationship('Role', secondary='roles_users',
                            backref=db.backref('users', lazy='dynamic'))

    # active = db.Column(db.Boolean, unique=False, server_default=0)

    def __init__(self, firstname, lastname, username, password, email, phone):
        self.firstname = firstname
        self.lastname = lastname
        self.username = username
        self.password = password
        self.email = email
        self.phone = phone


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False, unique=True)

    def __init__(self, role_name):
        self.role_name = role_name


class UserRoles(db.Model, RoleMixin):
    __tablename__ = 'roles_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column('role_id', db.Integer, db.ForeignKey('role.id'))


# user_datastore = SQLAlchemyUserDatastore(db, User, Role)
# app.security = Security(app, user_datastore)


def create_db():
    with app.app_context():
        db.create_all()


def create_default_user():
    user = User(firstname='admin',
                lastname='admin',
                username='admin',
                email='admin@admin.am',
                password=generate_hash('123456'),
                phone='123456')
    db.session.add(user)
    db.session.commit()


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[validators.DataRequired(message=em.username_required)])
    password = PasswordField('Password', validators=[validators.DataRequired(message=em.password_required)])


class RegisterForm(FlaskForm):
    firstname = StringField('Firstname', [validators.DataRequired(message=em.firstname_required)])
    lastname = StringField('Lastname', [validators.DataRequired(message=em.lastname_required)])
    username = StringField('Username',
                           [validators.DataRequired(message=em.username_required), validators.Length(min=4, max=100)])
    email = EmailField('Email',
                       [validators.DataRequired(message=em.email_required), validators.Length(min=4, max=100)])
    phone = StringField('Phone', [validators.DataRequired(message=em.phone_required)])
    password = PasswordField('Enter Password', [validators.DataRequired(message=em.password_required),
                                                validators.Length(min=6, max=20),
                                                validators.AnyOf(values=any_of_in_password,
                                                                 message="The password must have at least one character '!', '@', '#', '$', '%', '&', '*', '.'"),
                                                validators.EqualTo('password_confirm', message=em.password_match)])
    password_confirm = PasswordField('Re-enter password')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    form = LoginForm()
    if request.method == 'POST':
        data = request.form
        username = data['username']
        user = User.query.filter_by(username=username).first()
        if user:
            if data['username'] == user.username and data['password'] == user.password:
                login_user(user)
                return redirect(url_for('admin_dashboard', username=user.username))
            else:
                error_message = 'Wrong password'
                return render_template('admin/admin_login_form.html', form=form, error=error_message)
        else:
            error_message = 'Wrong username'
            return render_template('admin/admin_login_form.html', form=form, error=error_message)
    return render_template('admin/admin_login_form.html', form=form)


@app.route('/admin/logout')
def logout():
    logout_user()
    return redirect(url_for('admin'))


@app.route('/admin/dashboard')
@app.route('/admin/dashboard/<username>')
@login_required
def admin_dashboard(username):
    users = User.query.all()
    return render_template('admin/admin_dashboard.html', username=username, users=users)


@app.route('/admin/dashboard/delete/<user_id>')
@login_required
def admin_delete_user(user_id):
    user = User.query.filter_by(id=user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/daashboard/edit/<user_id>')
@login_required
def admin_edit_user(user_id):
    user = User.query.filter_by(id=user_id)
    data = request.form  # TODO chack from form data can not be empty
    user.firstname = data['firstname']
    user.lastname = data['lastname']
    user.username = data['lastname']
    user.email = data['email']
    user.phone = data['phone']
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/register', methods=['GET', 'POST'])
@login_required
def admin_register():
    form = RegisterForm()
    if request.method == 'POST':
        data = request.form
        user = User(firstname=data['firstname'],
                    lastname=data['lastname'],
                    username=data['username'],
                    password=generate_hash(data['password']),
                    email=data['email'],
                    phone=data['phone'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('admin/user_register_form.html', form=form)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        data = request.form
        user = User.query.filter_by(username=data['username']).first()
        if user:
            if data['username'] == user.username and data['password'] == user.password:
                login_user(user)
                return redirect(url_for('dashboard', username=user.username))
            else:
                error_message = 'Wrong password'
                return render_template('login_form.html', form=form, error=error_message)
        else:
            error_message = 'Wrong username'
            return render_template('login_form.html', form=form, error=error_message)
    return render_template('login_form.html', form=form)


@app.route('/dashboard/<username>')
@login_required
def dashboard(username):
    return f'<h1>Dashboard {username}</h1>'


@app.route('/course/add')
@login_required
def course_add():
    pass


@app.route('/course/add_source')
@login_required
def course_add_cource():
    pass


if __name__ == '__main__':
    app.run()
