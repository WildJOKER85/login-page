from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin, auth_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators, EmailField
from werkzeug.security import generate_password_hash

from config import Config
from constants import ErrorMessages as em, any_of_in_password

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy()
db.init_app(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)

    def __init__(self, firstname, lastname, username, password, email, phone):
        self.firstname = firstname
        self.lastname = lastname
        self.username = username
        self.password = password
        self.email = email
        self.phone = phone


class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False)


# class Role(db.Model, RoleMixin):
#     id = db.Column(db.Integer, primary_key=True)


def create_db():
    with app.app_context():
        db.create_all()


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


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    form = LoginForm()
    if request.method == 'POST':
        data = form.data
        username = data['username']
        user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one()
        if user:
            current_user = user
        return redirect(url_for('dashboard', username=current_user.username))
    return render_template('admin/admin_login_form.html', form=form)


@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    form = RegisterForm()
    if request.method == 'POST':
        data = request.form
        user = User(firstname=data['firstname'],
                    lastname=data['lastname'],
                    username=data['username'],
                    password=generate_password_hash(data['password']),
                    email=data['email'],
                    phone=data['phone'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('admin/user_register_form.html', form=form)


@app.route('/admin/dashboard')
@app.route('/admin/dashboard/<username>')
# @auth_required()
def dashboard(username):
    return render_template('admin/admin_dashboard.html')


if __name__ == '__main__':
    app.run()
