import re
import MySQLdb.cursors
from flask import Flask, render_template, redirect, url_for, request, session, jsonify,flash
from flask_mysqldb import MySQL
from scipy.optimize import fsolve
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime
from datetime import timedelta
import numpy as np
import uuid
from flask_mail import Mail,Message
from random import randint
import hashlib

app = Flask(__name__)
mysql = MySQL(app)
# mysql.init_app(app)

app.config['SECRET_KEY'] = 'DJFDKJSDFLJSDF;LSD'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pokermessiaH307864'
app.config['MYSQL_DB'] = 'bondcalculator'


app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"]=465
app.config["MAIL_USERNAME"]='assetmanagersservices@gmail.com'
app.config['MAIL_PASSWORD']='ablqxfnafcenwqzn'                    #you have to give your password of gmail account
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail=Mail(app)



from datetime import datetime, timedelta

matd = ''
settled = ''


def bond_price(yield_to_maturity, face_value, tenor, coupon_rate, settlement_date, maturity_date):
    global dirty_price

    yield_to_maturity = yield_to_maturity / 100
    coupon_rate = coupon_rate / 100

    adjusted_yield_maturity = yield_to_maturity / 2

    days_between_issue_and_maturity = tenor * 364
    # print(f"This is before  {maturity_date}")
    effective_issue_date = maturity_date - timedelta(days=days_between_issue_and_maturity)

    days_between = (settlement_date - effective_issue_date)

    no_of_half_years_between_deal_and_maturity = (days_between / 182)

    sec = no_of_half_years_between_deal_and_maturity + timedelta(days=1)
    sec_days = sec.days + sec.seconds // 86400

    starter = timedelta()

    for i in range(1, 183):
        starter += timedelta(days=sec_days)

    next_interest_payment_date = effective_issue_date + starter

    half_years_between_deal_and_next_interest_payment_date = (next_interest_payment_date - settlement_date) / 182

    yrs_d_interest = half_years_between_deal_and_next_interest_payment_date.total_seconds()
    yrs_d_interest = yrs_d_interest / 86400

    half_between_next_interest_date_and_maturity = (maturity_date - next_interest_payment_date) / 182

    int_date_and_mature = half_between_next_interest_date_and_maturity.days + half_between_next_interest_date_and_maturity.seconds // 86400

    one_plus_u = 1 / adjusted_yield_maturity * (1 - (1 + adjusted_yield_maturity) ** -int_date_and_mature) + 1
    dc = (face_value * coupon_rate / 2) * (one_plus_u / (1 + adjusted_yield_maturity) ** yrs_d_interest)
    dp = face_value / (1 + adjusted_yield_maturity) ** (yrs_d_interest + int_date_and_mature)
    dirty_price = np.round(dc + dp, 4)

    accrued_interest = np.round((face_value * coupon_rate / 2) * (1 - yrs_d_interest), 4)
    clean_price = np.round(dirty_price - accrued_interest, 4)

    dirty_percentage = np.round((dirty_price / face_value) * 100, 4)
    clean_percentage = np.round((clean_price / face_value) * 100, 4)

    print('----------------------------------------------------------------|')
    print(f"DIRTY PRICE = {dirty_price}")
    print(f"ACCRUED INTEREST = {accrued_interest}")
    print(f"CLEAN PRICE = {clean_price}")
    print(f"Dirty Price(%): {dirty_percentage}                              |")
    print(f"CLEAN PRICE (%) = {clean_percentage}")
    print('---------------------------------------------------------------|')
    return dirty_price, clean_price, dirty_percentage, clean_percentage, dc, dp, one_plus_u, accrued_interest


@app.route("/form1/home", methods=['GET'])
def home():
    global matd
    maturity_date = request.args.get('maturity_date')
    matd = maturity_date
    print(f"This is {matd}")

    if maturity_date is None:
        print("none for now")

    
    else:
        maturity_d, identifier = maturity_date.split('_')
       # continue with the rest of your code
        cur = mysql.connection.cursor()

        if identifier == "second":
            cur.execute("SELECT yield, face_value, tenor, coupon_rate FROM portfolio WHERE maturity_date = %s ORDER BY security_id ASC LIMIT 1,1", (maturity_d,))
            # cur.execute("SELECT yield, face_value, tenor, coupon_rate FROM portfolio WHERE maturity_date = %s ORDER BY security_id DESC LIMIT 1", (maturity_date,))
            result = cur.fetchall()
            print(f"all i wanted {result}")

           
            
            session['yield_2'] = result[0][0]
            print(session['yield_2'])
            session['face_value_2'] = result[0][1]
            print(session['face_value_2'])
            session['tenor_2'] = result[0][2]
            session['coupon_rate_2'] = result[0][3]

            if result is not None:
                return jsonify({
                'yield': result[0][0],
                    'face_value': result[0][1],
                    'tenor': result[0][2],
                    'coupon_rate': result[0][3]
            })
                
            else:
                print("It is none")

        else:

            cur.execute("SELECT yield, face_value, tenor, coupon_rate FROM portfolio WHERE maturity_date = %s ORDER BY security_id ASC LIMIT 1", (maturity_d,))
            result = cur.fetchone()

            facevalue = 0
            tenor = 0
            Yield = 0
            Coupon_rate = 0
            session['yield'] = Yield
            session['face_value'] = facevalue
            session['tenor'] = tenor
            session['coupon_rate'] = Coupon_rate
            session['maturity_d'] = maturity_d

            if result is not None:
                return jsonify({
                    'yield': result[0],
                    'face_value': result[1],
                    'tenor': result[2],
                    'coupon_rate': result[3]
                })
            else:
                print("It is none")       
    return render_template("home.html")



@app.route("/form1/home", methods=['POST', 'GET'])
def finder():
    if request.method == 'POST':
        
            face_value = int(request.form['face_value'])
            yield_to_maturity = float(request.form['yield'])
            tenor = int(request.form['tenor'])            
            settlement_date = datetime.strptime(request.form['settlementdate'], '%Y-%m-%d')
            coupon_rate = float(request.form['coupon_rate'])


            maturity_date = session['maturity_d']
            maturity_date = datetime.strptime(maturity_date, '%Y-%m-%d')

            dirty_price, clean_price, dirty_percentage, clean_percentage, dc, dp, one_plus_u, accrued_interest = bond_price(
                yield_to_maturity,
                face_value,
                tenor,
                coupon_rate,
                settlement_date,
                maturity_date)

            session['yield'] = yield_to_maturity
            session['face_value'] = face_value
            session['tenor'] = tenor
            session['coupon_rate'] = coupon_rate
            session['settlementdate'] = settlement_date

            return render_template("yield.html",
                                   dirty_price=dirty_price,
                                   clean_price=clean_price,
                                   dirty_percentage=dirty_percentage,
                                   clean_percentage=clean_percentage,
                                   dc=dc,
                                   dp=dp,
                                   one_plus_u=one_plus_u,
                                   accrued_interest=accrued_interest)



@app.route("/form2/yield", methods=['POST'])
def findyield():
    desired_price = float(request.form.get('desired_price'))
    market_yield = float(request.form.get('market_yield'))

    face_value = session['face_value']
    tenor = session['tenor']
    coupon_rate = session['coupon_rate']
    settlement_date = session['settlementdate']
    settlement_date = settlement_date.replace(tzinfo=None)
    maturity_date = session['maturity_d']
    maturity_date = datetime.strptime(maturity_date, '%Y-%m-%d')

    def clean_percentage_error(yield_to_maturity, face_value, tenor,
                               coupon_rate, settlement_date, maturity_date):
        _, _, _, clean_percentage, _, _, _, _ = bond_price(yield_to_maturity, face_value, tenor, coupon_rate,
                                                           settlement_date, maturity_date)

        return clean_percentage - desired_price

    import numpy as np
    initial_guess = 0.05
    solution = fsolve(clean_percentage_error, initial_guess,
                      args=(face_value, tenor, coupon_rate, settlement_date, maturity_date))

    solutionfest = np.round(solution[-1], 2)
    firstdirty = solution[0]
    print(f"First :{firstdirty}")

    dirty = bond_price(firstdirty, face_value, tenor, coupon_rate,
                       settlement_date, maturity_date)

    Normal_dirty = dirty[0]
    session['normal_dirty'] = Normal_dirty
    session['solutionfest'] = solutionfest
    print(f"This is dirty: {Normal_dirty}")

    market_dirty = bond_price(market_yield, face_value, tenor, coupon_rate,
                              settlement_date, maturity_date)

    # print(market_dirty[0])
    marketcond = round(market_dirty[0], 4)

    session['marketcond'] = marketcond

    Buyers_losses = round(marketcond - Normal_dirty, 4)
    # print((Buyers_losses))

    return render_template('SellingYield.html', solutionfest=solutionfest, Normal_dirty=Normal_dirty,
                           marketcond=marketcond, Buyers_losses=Buyers_losses)


@app.route("/buy", methods=['POST'])
def buy():
    if request.method == 'POST':
        try:
            f_value = float(request.form['f_value'])
            yielb = float(request.form['yielb'])
            t_nor = int(request.form['t_nor'])
            c_rate = float(request.form['c_rate'])
            settlement = datetime.strptime(request.form['settlement'], '%Y-%m-%d')
            maturity = datetime.strptime(request.form['maturity'], '%Y-%m-%d')

            dirty_price, clean_price, dirty_percentage, clean_percentage, dc, dp, one_plus_u, accrued_interest = bond_price(
                yielb, f_value, t_nor, c_rate,
                settlement, maturity)

            marketdirty = session.get('marketcond')
            print(f"This market: {marketdirty}")

            First_selling_dirty = session.get('normal_dirty')

            def solve_for_face_value(f_value, marketdirty, yielb, t_nor, c_rate, settlement, maturity):
                Dirty_Price, _, _, _, _, _, _, _ = bond_price(yielb, f_value, t_nor, c_rate,
                                                              settlement, maturity)
                return Dirty_Price - marketdirty

            initial_guess = 100
            solve_face = fsolve(solve_for_face_value, initial_guess,
                                args=(marketdirty, yielb, t_nor, c_rate, settlement, maturity))
            # print(solve_face[0])
            face = round(solve_face[0], 0)

            def dirty_price_error(yielb, face, t_nor, c_rate, settlement, maturity):
                First_dirt, _, _, _, _, _, _, _ = bond_price(yielb, face, t_nor, c_rate,
                                                             settlement, maturity)

                return First_dirt - First_selling_dirty

            first_guess = 0.05

            import math
            final_sol = fsolve(dirty_price_error, first_guess, args=(face, t_nor, c_rate, settlement, maturity))

            Final_Yield = np.round(final_sol[-1], 2)
            print(Final_Yield)
            SELL = session.get('solutionfest')
            return render_template("Buydetails.html",
                                   dirty_price=dirty_price,
                                   clean_price=clean_price,
                                   dirty_percentage=dirty_percentage,
                                   clean_percentage=clean_percentage,
                                   dc=dc,
                                   dp=dp,
                                   one_plus_u=one_plus_u,
                                   accrued_interest=accrued_interest, face=face,SELL = SELL, Final_Yield=Final_Yield)
        except (ValueError, TypeError) as e:
            return jsonify({'error': 'Invalid form data'})
        



@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/sign-up', methods=['GET', 'POST'])
def signup():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'firstName' in request.form \
            and 'password1' in request.form and 'password2' in request.form:
        email = request.form['email']
        first_name = request.form['firstName']
        password1 = request.form['password1']
        password2 = request.form['password2']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM user_system WHERE email = %s", (email,))
        account = cursor.fetchone()

        if account:
            mesage = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            mesage = 'Invalid email address !'
        elif not first_name or not password1 or not email or not password2:
            mesage = 'Please fill out the form !'
        else:
            password1 = generate_password_hash(password1)
            cursor.execute("INSERT INTO user_system(name,email,password) VALUES (%s,%s,%s)",
                           (first_name, email, password1))
            mysql.connection.commit()
            mesage = 'You have successfully registered !'
    elif request.method == 'POST':
        mesage = 'Please fill out the form !'
    return render_template("sign_up.html", mesage=mesage)


@app.route('/', methods=['POST', 'GET'])
def login():
    mesage = ''
    if 'login' in request.form:
        if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
            email = request.form["email"]
            password = request.form["password"]
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("select * from user_system where email=%s", (email,))
            user = cur.fetchone()
            if user and check_password_hash(user['password'], password):
                session['loggedin'] = True
                session['email'] = user['email']
                session['password'] = user['password']
                mesage = 'Logged in successfully !'
                return redirect(url_for('dashboard'))
            else:
                mesage = 'Please enter correct email / password !'
    return render_template('login.html', mesage=mesage)

@app.route('/dashboard', methods = ['GET'])
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT YEAR(maturity_date), Book_value FROM security")
    data = cur.fetchall()

    if data:
        year_values = {}
        for row in data:
            year = row[0]
            value = row[1]
            if year in year_values:
                year_values[year] += value
            else:
                year_values[year] = value

        sorted_years = sorted(year_values.keys())        

        # labels = [row[0].strftime("%Y-%m-%d") for row in data]
        labels = [str(year) for year in sorted_years]
        values = [year_values[year] for year in sorted_years]

        # labels = [row[0] for row in data]
        # values = [row[1] for row in data]

    cur.execute("SELECT SUM(Face_value) FROM security WHERE Security_class ='Cash'")
    cash_total = cur.fetchone()[0]

    cur.execute("SELECT SUM(Face_value) FROM security WHERE Security_class ='Income'")
    income_total = cur.fetchone()[0]

    cur.execute("SELECT SUM(Face_value) FROM security WHERE Security_class ='Yield'")
    yield_total = cur.fetchone()[0]



    cur.execute("SELECT SUM(Face_value) FROM security WHERE Coupon_class ='High coupon'")
    hc_total = cur.fetchone()[0]

    cur.execute("SELECT SUM(Face_value) FROM security WHERE Coupon_class ='Mid coupon'")
    mc_total = cur.fetchone()[0]

    cur.execute("SELECT SUM(Face_value) FROM security WHERE Coupon_class ='Low coupon'")
    lc_total = cur.fetchone()[0]

    cur.execute("SELECT SUM(Book_value) FROM security ")
    bk_total = cur.fetchone()[0]

    cur.execute("SELECT SUM(Face_value) FROM security ")
    fc_total = cur.fetchone()[0]

    cur.execute("SELECT SUM(Market_value) FROM security ")
    mk_total = cur.fetchone()[0]

    # Define the colors for the chart
    colors = ['#FF6384', '#36A2EB', '#FFCE56']

    return render_template("graph.html", labels=labels, values=values,cash_total=cash_total, income_total=income_total,
                           yield_total=yield_total, colors=colors, hc_total=hc_total, mc_total=mc_total, lc_total=lc_total, bk_total=bk_total, fc_total=fc_total, mk_total=mk_total)


# otp=randint(000000,999999)

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    return render_template("forgot.html")

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    mess = "One time password has been sent to the mail id. please check"
    email = None
    global specific 
    
    if request.method == "POST":
        global otp
        otp = randint(000000, 999999)  # generate a new OTP
        print(otp)
        session['otp'] = otp  # store the OTP in the session
        
        if 'email' in request.form:
            email = request.form['email']
            specific = email
            print(f"This is the specific oo {specific}")
            
            message = "This is a one-time verification code. Your code is: {}".format(otp)
            
            msg = Message(subject='OTP', sender='assetmanagersservices@gmail.com', recipients=[email])
            msg.body = message
            mail.send(msg)
    
    return render_template('verify.html', mess=mess)


# @app.route('/verify', methods=['GET', 'POST'])
# def verify():
#     mess = "One time password has been sent to the mail id. please check"
#     email = None
#     global specific 
    
#     if request.method == "POST":
#         global otp
#         otp = randint(000000, 999999)  # generate a new OTP
#         print(otp)
#         session['otp'] = otp  # store the OTP in the session
#         message = "This is a one-time verification code. Your code is: {}".format(otp)
#         email = request.form['email']   
#         specific = email
#         print(f"This is the specific oo {specific}")     
        
#         msg = Message(subject='OTP', sender='assetmanagersservices@gmail.com', recipients=[email])
#         msg.body = message
#         mail.send(msg)
    
#     return render_template('verify.html', mess=mess)

@app.route('/validate', methods=['POST'])
def validate():
    news = ""
    error = ""

    if request.method == "POST":
        user = request.form.get("otp")
        if user and int(user) == session.get('otp', -1):
            return render_template("reset_password.html")
        else:
            error = "Incorrect OTP. Please try again."           
            return render_template("verify.html", error=error)
    
    return render_template("reset_password.html")

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    message = ''
    
    if request.method == 'POST' and 'password' in request.form and 'confirm' in request.form:
        password = request.form['password']
        confirm = request.form['confirm']

        if password == confirm:
            hashed_new_password = generate_password_hash(password)
            cur = mysql.connection.cursor()
            cur.execute("UPDATE user_system SET password = %s WHERE email = %s", (hashed_new_password, specific))
            mysql.connection.commit()
            message = 'Password updated successfully'
            return redirect(url_for('login', suc=message))
        else:
            message = 'Passwords do not match'

    return render_template('reset_password.html', message=message)



@app.route('/updated', methods= ['GET','POST'])
def updated():
    return render_template("updatedPass.html")

          




@app.route('/form', methods=['POST', 'GET'])
def form():
    if request.method == 'POST':
        option = request.form['name']
        curs = mysql.connection.cursor()
        curs.execute("SELECT name FROM form where name = %s", (option,))
        row = curs.fetchall()
        # field1 = row[0]
        # field2 = row[1]

        return render_template("form.html", sika=row)

    return render_template("form.html")





if __name__ == "__main__":
    app.run(debug=True)
