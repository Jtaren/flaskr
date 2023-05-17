from flask import Flask, render_template, flash, request, redirect, url_for
from  flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import TextArea
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

# Create a Flask Instance
app = Flask(__name__)
app.config['SECRET_KEY'] = "my secret key no one should know"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/blog'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.app_context().push()

# Json Thing
# @app.route('/date')
# def get_current_date():
#     return {"Date": date.today()}

#Create a Blog Post Model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255))

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    favorite_color = db.Column(db.String(120))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not readable attribute!')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)    

    def __repr__(self):
        return '<Name %r>' % self.name
#Create a Form Class
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    favorite_color = StringField("Favorite Color")
    password_hash = PasswordField("Password", validators=[DataRequired(), EqualTo('password_hash2', message='Password must match')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField("Submit")

class PasswordForm(FlaskForm):
    email = StringField("What's your Email?", validators=[DataRequired()])
    password_hash = PasswordField("What's Your Password?")
    submit = SubmitField("Submit")    

class NameForm(FlaskForm):
    name = StringField("What's your Name?", validators=[DataRequired()])
    submit = SubmitField("Submit")

class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = StringField("Content",validators=[DataRequired()], widget=TextArea() )
    author = StringField("Author", validators=[DataRequired()])
    slug = StringField("slug", validators=[DataRequired()])
    submit = SubmitField("Submit", )

@app.route('/posts')
def posts():
    # Grab all the posts from the database
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html", posts=posts)


@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template("post.html", post=post)

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.author = form.author.data
        post.slug = form.slug.data
        post.content = form.content.data

        #Update to database
        db.session.add(post)
        db.session.commit()
        flash("Post Has Been Updated") 
        return redirect(url_for('post', id=post.id))
    form.title.data = post.title
    form.author.data = post.author
    form.slug.data = post.slug
    form.content.data = post.content
    return render_template('edit_post.html', form=form)



#Add Post Page
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Posts(title=form.title.data, content=form.content.data, author=form.author.data, slug=form.slug.data)
        form.title.data = ''
        form.content.data = ''
        form.author.data = ''
        form.slug.data = ''

        #Add post data to database
        db.session.add(post)
        db.session.commit()

        #Return a Message
        flash("Blog Post Submitted Successfully")
    #Redirect to the webpage
    return render_template("add_post.html", form=form)    

# def index():
#    return "<h1>Hello World!</h1>"

#FILTERS
#safe
#capitalize
#lower
#upper
#title
#trim
#striptags

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(name=form.name.data, email=form.email.data, favorite_color=form.favorite_color.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.email.data = ''  
        form.favorite_color.data = ''
        form.password_hash = ''
        flash("User Added Successfully!") 
    our_users =  Users.query.order_by(Users.date_added)     
    return render_template("add_user.html", form=form, name=name, our_users=our_users)

# Craete a route decorator
@app.route('/')
def index():
    name=None
    first_name="John"
    stuff = "this is bold text"

    favourite_pizza = ["Pepperoni", "Cheese", "Mushrooms", 41]
    return render_template("index.html", first_name=first_name,
     stuff=stuff, favourite_pizza=favourite_pizza)
# localhost:5000/user/john
@app.route('/user/<name>')
def user(name):
    return render_template("user.html", user_name=name)
   

# Create Password Test Page
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()
    #Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        #Clear the form
        form.email.data = ''
        form.password_hash.data = ''

        pw_to_check = Users.query.filter_by(email=email).first()
        #flash("Form Submitted Sucessfully")

        passed = check_password_hash(pw_to_check.password_hash, password)
    return render_template("test_pw.html", email=email, password = password, form=form, pw_to_check=pw_to_check, passed=passed)


# Create Name Page
@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form = NameForm()
    #Validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Form Submitted Sucessfully")
    return render_template("name.html", name=name, form=form)


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        try:       
            db.session.commit()
            flash("User Updated Successfully!") 
            return render_template("update.html", form=form, name_to_update=name_to_update)
        except:
            flash("Error! Looks like there was a problem")
            return render_template("update.html", form=form, name_to_update=name_to_update)
    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id = id)
    
@app.route('/delete/<int:id>')
def delete(id):
    name = None
    form = UserForm()
    user_to_delete = Users.query.get_or_404(id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully")
        our_users = Users.query.order_by(Users.date_added)
        return render_template("add_user.html", form=form, name=name, our_users=our_users)
    except:
        flash("Whoops! There was a problem deleting user...try again!")
        return render_template("add_user.html", form=form, name=name, our_users=our_users)


        
       

# def user(name):
#    return "<h1>Hello {}!!!</h1>".format(name)

# CreatevCustom Error Pages

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(404)
def page_not_found(e):
    return render_template("500.html"), 500

