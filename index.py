#IMPORT
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
app=Flask(__name__)
app.secret_key="templateblog"

#MYSQLDB CONNECT
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "flaskblog"
app.config["MYSQL_CURSORCLASS"]= "DictCursor"
mysql= MySQL(app)


#REGISTER FORM
class form_register(Form):
    username = StringField("Username",validators=[
        validators.Length(min=4,max=20),
        validators.DataRequired()])
    
    email= StringField("Email",validators=[
        validators.DataRequired(),
        validators.Email(message="Please entry real email.")])
   
    password = PasswordField("Password",validators=[
        validators.Length(min=8,max=26),
        validators.DataRequired(message="Required")])
    
    confirm= PasswordField("Confirm Password",validators=[
        validators.Length(min=8,max=26),
        validators.EqualTo(fieldname="password"),
        validators.DataRequired(message="Required")])
    
#LOGIN FORM
class form_login(Form):
    username=StringField("Username")
    password=PasswordField("Password")

#ARTICLE FORM
class form_article(Form):
    title=StringField("Title",validators=[validators.Length(min=5,max=70)])
    content=TextAreaField("Content",validators=[validators.Length(min=10)])

#ROUTE
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
    
@app.route("/login",methods =["GET","POST"])
def login():
    form=form_login(request.form)
    if request.method == "POST":
        username=form.username.data
        password_entered=form.password.data

        cursor=mysql.connection.cursor()
        query= "SELECT * FROM users where username= %s"
        result=cursor.execute(query,(username,))
        
        if result>0:
            data=cursor.fetchone()
            real_pass=data["password"]
            if sha256_crypt.verify(password_entered,real_pass):
                flash("Login Successful","success")
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("home"))
            else:
                flash("Wrong Password","danger")
                return redirect(url_for("login"))
        else:
            flash("Wrong username","danger")
            return redirect(url_for("login"))
     
    
    return render_template("login.html", form = form)

@app.route("/register",methods =["GET","POST"])
def register():
    form=form_register(request.form)
    
    if request.method== "POST" and form.validate():
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(form.password.data)
        
        cursor=mysql.connection.cursor()

        query = "Insert into users (email,username,password) VALUES(%s,%s,%s)"
        cursor.execute(query,(email,username,password))
        mysql.connection.commit()   
        cursor.close()

        flash("Registration successful..","success")

        return redirect(url_for("login"))
    
    else:
        return render_template("register.html",form=form)

@app.route("/projects")
def projects():
    return render_template("projects.html")

#USER DECORATOR
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please Login for this page.","danger")
            return redirect(url_for("login"))
    return decorated_function

@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu= "SELECT * FROM article where author=%s"
    result=cursor.execute(sorgu,(session["username"],))
    if result > 0:
        article=cursor.fetchall()
        return render_template("dashboard.html",article=article)
        
    else:
        return render_template("dashboard.html")
        
    

@app.route("/posts")
def posts():
    cursor=mysql.connection.cursor()
    query= "SELECT * FROM article"
    result=cursor.execute(query)
    if result>0:
        article= cursor.fetchall()

        return render_template("posts.html",article=article)
    else:
        return render_template("posts.html")
    

@app.route("/posts/<string:id>")
def post(id):
    cursor=mysql.connection.cursor()
    query= "SELECT * FROM article WHERE id = %s"
    result=cursor.execute(query,(id,))
    if result >0:
        article=cursor.fetchone()
        return render_template("post.html",article=article)

    else:
        return render_template("post.html")

@app.route("/addarticle",methods = ["GET","POST"])
def article():
    form=form_article(request.form)
    if request.method== "POST" and form.validate():
        title= form.title.data
        content=form.content.data
        
        cursor= mysql.connection.cursor()

        sorgu= "INSERT INTO article(title,author,content) VALUES(%s,%s,%s) " 
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()

        cursor.close()
        flash("Successfully Added.","success")
        return redirect(url_for("dashboard"))
    

    return render_template("addarticle.html",form=form)

#RUN
if __name__=="__main__":
 app.run(debug=True)