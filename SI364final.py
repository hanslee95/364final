###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from flask_script import Manager, Shell
from wtforms import RadioField, StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError, IntegerField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
import requests
import simplejson as json
from random import randint

# Imports for login management
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
 

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'hard to guess string from si364'
##Used createdb midterm to create db on postico which made the localhost work. Maybe work on name insertion that takes you
##to name of person with their favorite pokemons.
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/si364finalhanheum"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
manager = Manager(app)
db = SQLAlchemy(app) # For database use
migrate = Migrate(app, db) # For database use/updating
manager.add_command('db', MigrateCommand)

# Login configurations setup
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) # set up login manager

## Set up Shell context so it's easy to use the shell to debug
# Define function
def make_shell_context():
    return dict(app=app, db=db, User=User)

# Add function use to manager
manager.add_command("shell", Shell(make_context=make_shell_context))

######################################
######## HELPER FXNS (If any) ########
######################################

def get_pokemon_by_id(id):
    """Should return pokemon object or None"""
    p = Pokemon.query.filter_by(user_id=id).first()
    return p

def get_or_create_pokemon(db_session, poke_name, poke_hp, url, current_user):
    pokemon = db_session.query(Pokemon).filter_by(poke_name = poke_name, user_id = current_user.id).first()
    if pokemon:
        return pokemon
    else:
        pokemon = Pokemon(poke_name = poke_name, embedURL = url, hp = poke_hp, user_id = current_user.id)
        db_session.add(pokemon)
        db_session.commit()
        return pokemon

def get_or_create_personalroster(db_session, trainer_name, current_user, poke_lst = []):
    personalroster = db_session.query(PersonalRoster).filter_by(trainer_name = trainer_name, user_id = current_user.id).first()
    if personalroster:
        return personalroster
    else:
        personalroster = PersonalRoster(trainer_name= trainer_name, user_id = current_user.id, pokemon = [])

        for elem in poke_lst:
            personalroster.pokemon.append(elem)
        db_session.add(personalroster)
        db_session.commit()
        return personalroster

def get_or_create_pictures(db_session, poke_name, url):
    pictures = db_session.query(Pictures).filter_by(poke_name = poke_name).first()
    if pictures:
        return pictures
    else:
        pictures = Pictures(poke_name = poke_name, embedURL = url)
        db_session.add(pictures)
        db_session.commit()
        return pictures






##################
##### MODELS #####
##################

#Association Table between pokemon and roster.
trainer_roster = db.Table('trainer_roster',db.Column('pokemon_id', db.Integer, db.ForeignKey('pokemon.id')),db.Column('personalroster_id',db.Integer, db.ForeignKey('personalroster.id')))


## User Models
# Special model for users to log in
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    trainer_name = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    gender = db.Column(db.String(64))
    pokemons = db.relationship('Pokemon', backref = 'User')
    personalroster = db.relationship('PersonalRoster', backref = 'User')
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

## DB load function
## Necessary for behind the scenes login manager that comes with flask_login capabilities! Won't run without this.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # returns User object or None  


#Model to store pokemon and hit points (hp).
class Pokemon(db.Model):
    __tablename__ = "pokemon"
    id = db.Column(db.Integer,primary_key=True)
    poke_name = db.Column(db.String(128))
    embedURL = db.Column(db.String(256))
    hp = db.Column(db.Integer)
    # This model should have a one-to-many relationship with the User model (one user, many personal pokemons 
    # with different names.)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # This shows the poke name, id, and the url of the pokemon info.
    def __repr__(self):
        return "{} (ID: {}) (URL: {})".format(self.poke_name, self.id, self.embedURL)


# Model to store a trainer's pokemon roster
class PersonalRoster(db.Model):
    __tablename__ = 'personalroster'
    id = db.Column(db.Integer, primary_key = True)
    trainer_name = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # This model should also have a many to many relationship with the Pokemon model (one pokemon might be in many personal rosters, 
    # one personal roster could have many pokemon in it).
    pokemon = db.relationship('Pokemon',secondary=trainer_roster,backref=db.backref('personalroster',lazy='dynamic'),lazy='dynamic')
      

class Pictures(db.Model):
    __tablename__ = 'pictures'
    id = db.Column(db.Integer, primary_key = True)
    poke_name = db.Column(db.String(128))
    embedURL = db.Column(db.String(256))




###################
###### FORMS ######
###################

##### Set up Forms #####

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    trainer_name = StringField('trainer_name:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Names must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    #Additional checking methods for the form
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class NumberForm(FlaskForm):
    number = IntegerField('Enter a number between 1-151:', validators =[Required()])
    submit = SubmitField('Submit')   

class TypeForm(FlaskForm):
    types = RadioField('Choose a pokemon type:', choices =[('flying', 'flying'),('normal','normal'),('fighting','fighting'),
        ('poison','poison'),('ghost','ghost'),('pink','pink'),('electric','electric'),('red','red'),('dragon','dragon'),
        ('fairy','fairy'), ('water','water')], validators = [Required()]) 
    submit = SubmitField('Submit')

class CreateCollectionForm(FlaskForm):
    trainer_name = StringField('Enter your trainer name exactly. (Can be found on top left corner in BOLD):',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Names must have only letters, numbers, dots or underscores')])
    submit = SubmitField('Create')



#######################
###### VIEW FXNS ######
#######################




## Login-related routes - provided
@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('number'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('base'))

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,trainer_name=form.trainer_name.data,password=form.password.data)
        #saving this name for power model
        
        db.session.add(user)
        db.session.commit()

       

        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/secret')
@login_required
def secret():
    return "Only authenticated users can do this! Try to log in or contact the site admin."





#############Decorators##############





#This will show a search bar to put in your favorite number. Will render a template that will show that you added a certain pokemon to your
#roster.
@app.route('/')
def base():
    return render_template('base.html')

@app.route('/number', methods=["GET","POST"])
@login_required
def number():
    form = NumberForm() 
    if form.validate_on_submit:

        return render_template('number.html', form = form)    

#shows what you added by filling in your number and also the next options which is different types you can choose from.
@app.route('/postnumber', methods=["GET","POST"])
@login_required
def post_number():
    form = NumberForm()
    form2 = TypeForm()
    result = requests.get('https://pokeapi.co/api/v2/pokemon/{}/?limit=151&offset=0'.format(form.number.data))
    url = 'https://pokeapi.co/api/v2/pokemon/{}/?limit=151&offset=0'.format(form.number.data)
    poke_dict = json.loads(result.text)
    #getting access to the pokemon name
    poke_name = poke_dict['name']
    #getting the hp (strength) of the pokemon
    poke_hp = poke_dict['stats'][5]['base_stat']

    embedurl = poke_dict['sprites']['front_default']
    if form.validate_on_submit:
        get_or_create_pokemon(db.session, poke_name, poke_hp, url, current_user)
        get_or_create_pictures(db.session, poke_name, embedurl)


  
        return render_template('post_number.html', poke_name = poke_name, poke_hp = poke_hp, form = form2)

#this is to get the actual name/hp of the pokemon with the chosen type. 
@app.route('/types',methods=["GET","POST"])
@login_required
def types():
    form = TypeForm()
    result = requests.get('https://pokeapi.co/api/v2/type/{}/?limit=151&offset=0'.format(form.types.data))
    poke_dict = json.loads(result.text)
    length = len(poke_dict['pokemon'])
    poke_name = poke_dict['pokemon'][randint(0, length-1)]['pokemon']['name']

    #getting the hp for this pokemon
    result_name = requests.get('https://pokeapi.co/api/v2/pokemon/{}/?limit=151&offset=0'.format(poke_name))
    url = 'https://pokeapi.co/api/v2/pokemon/{}/?limit=151&offset=0'.format(poke_name)
    poke_dict_name = json.loads(result_name.text)
    poke_hp = poke_dict_name['stats'][5]['base_stat']

    embedurl = poke_dict_name['sprites']['front_default']
    if form.validate_on_submit:
        get_or_create_pokemon(db.session, poke_name, poke_hp, url, current_user)
        get_or_create_pictures(db.session, poke_name, embedurl)



    
        return render_template('type.html', poke_name = poke_name, poke_hp = poke_hp)

    


#List out all the pokemon discovered so far.
@app.route('/allpokemon')
def discovered_pokemon():
    pokemon = Pokemon.query.all()
    pokemon_discovered = []
    for p in pokemon: 
        tup = (p.poke_name, p.hp)
        pokemon_discovered.append(tup)
    return render_template('discovered_pokemon.html',pokemon_discovered= pokemon_discovered) 

@app.route('/create_collection',methods=["GET","POST"])
@login_required
def create_collection():
    form = CreateCollectionForm()
    return render_template('create_collection.html', form = form) 

@app.route('/collections',methods=["GET","POST"])
@login_required
def collections():
    lst =[]
    form = CreateCollectionForm()
    pokemon = Pokemon.query.all()
    choices = [(p.user_id, p.poke_name) for p in pokemon]
    if form.validate_on_submit:
        for p_id in choices:
            lst.append(get_pokemon_by_id(p_id[0]))

        get_or_create_personalroster(db.session, form.trainer_name.data, current_user, lst)

    collections = User.query.all()
    return render_template('collections.html', collections = collections, trainer = form.trainer_name.data )

@app.route('/collection/<id_num>')
def single_collection(id_num):
    id_num = int(id_num)
    collection = PersonalRoster.query.filter_by(id=id_num).first()
    pokemon = Pokemon.query.filter_by(user_id = id_num).all()
    return render_template('collection.html',collection=collection, pokemon=pokemon)

@app.route('/pictures')
def pictures():
    pictures = Pictures.query.all()
    return render_template('pictures.html', all_pics = pictures)



    

#######################
###### ERROR HANDLER ######
#######################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


## Code to run the application...
if __name__ == '__main__':
    db.create_all()
    manager.run()

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
