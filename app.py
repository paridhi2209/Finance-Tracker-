from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "finance_secret"



# DATABASE SETUP


def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    # USERS
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

    # TRANSACTIONS
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            type TEXT,
            user_id INTEGER
        )
    ''')

    # EMI TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS emis(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            amount REAL,
            due_date TEXT,
            user_id INTEGER
        )
    ''')

    # SAVINGS GOALS
    c.execute('''
        CREATE TABLE IF NOT EXISTS savings_goals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_name TEXT,
            target_amount REAL,
            target_date TEXT,
            user_id INTEGER
        )
    ''')

    # STUDENT PROFILE
    c.execute('''
        CREATE TABLE IF NOT EXISTS student_profile(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monthly_budget REAL,
            user_id INTEGER
        )
    ''')

    # AFFORD CHECK
    c.execute('''
        CREATE TABLE IF NOT EXISTS afford_checks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            item_price REAL,
            user_id INTEGER
        )
    ''')

    # SPLIT EXPENSES
    c.execute('''
        CREATE TABLE IF NOT EXISTS split_expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            friend_name TEXT,
            amount REAL,
            description TEXT,
            user_id INTEGER
        )
    ''')

    conn.commit()
    conn.close()


init_db()


# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():

    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # TRANSACTIONS
    c.execute(
        "SELECT * FROM transactions WHERE user_id=?",
        (session['user_id'],)
    )

    transactions = c.fetchall()

    total_income = 0
    total_expense = 0

    for t in transactions:

        if t['type'] == 'income':
            total_income += t['amount']

        else:
            total_expense += t['amount']

    balance = total_income - total_expense

    # AI SUGGESTIONS
    suggestion = ""

    if total_expense > total_income:
        suggestion = "⚠️ Your expenses are higher than your income!"

    elif balance > 5000:
        suggestion = "✅ Great job! Your savings look healthy."

    elif total_expense > 0.7 * total_income:
        suggestion = "💡 Try reducing your expenses to save more."

    else:
        suggestion = "✅ Your finances look balanced."

    # CATEGORY ANALYTICS
    food_total = 0
    travel_total = 0
    shopping_total = 0
    salary_total = 0

    for t in transactions:

        if t['category'] == 'Food':
            food_total += t['amount']

        elif t['category'] == 'Travel':
            travel_total += t['amount']

        elif t['category'] == 'Shopping':
            shopping_total += t['amount']

        elif t['category'] == 'Salary':
            salary_total += t['amount']

    # BUDGET WARNING
    budget_warning = ""

    if food_total > 5000:
        budget_warning = "🍔 Food budget exceeded!"

    elif shopping_total > 7000:
        budget_warning = "🛍️ Shopping budget exceeded!"

    elif travel_total > 4000:
        budget_warning = "✈️ Travel budget exceeded!"

    # AI INSIGHT
    ai_insight = ""

    highest = max(food_total, shopping_total, travel_total)

    if highest == food_total and food_total > 0:
        ai_insight = "🍔 Food is your highest spending category."

    elif highest == shopping_total and shopping_total > 0:
        ai_insight = "🛍️ Shopping is your highest spending category."

    elif highest == travel_total and travel_total > 0:
        ai_insight = "✈️ Travel is your highest spending category."

    # EMI SECTION
    c.execute(
        "SELECT * FROM emis WHERE user_id=?",
        (session['user_id'],)
    )

    emis = c.fetchall()

    emi_alerts = []

    today = datetime.now().date()

    for emi in emis:

        due = datetime.strptime(
            emi['due_date'],
            "%Y-%m-%d"
        ).date()

        days_left = (due - today).days

        if days_left < 0:

            emi_alerts.append(
                f"❌ {emi['name']} EMI is OVERDUE!"
            )

        elif days_left <= 3:

            emi_alerts.append(
                f"⚠️ {emi['name']} EMI due in {days_left} day(s)"
            )

    # SAVINGS GOALS
    c.execute(
        "SELECT * FROM savings_goals WHERE user_id=?",
        (session['user_id'],)
    )

    goals = c.fetchall()

    goal_insights = []

    for goal in goals:

        target_date = datetime.strptime(
            goal['target_date'],
            "%Y-%m-%d"
        ).date()

        days_left = (target_date - today).days

        months_left = max(days_left // 30, 1)

        monthly_saving = (
            float(goal['target_amount'])
            / months_left
        )

        goal_insights.append(
            f"🎯 {goal['goal_name']} → Save ₹{monthly_saving:.0f}/month"
        )

    # DAILY LIMIT
    c.execute(
        '''
        SELECT * FROM student_profile
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
        ''',

        (session['user_id'],)
    )

    profile = c.fetchone()

    daily_limit = None

    if profile:

        monthly_budget = profile['monthly_budget']

        remaining_money = (
            monthly_budget - total_expense
        )

        today_date = datetime.now()

        days_left = max(30 - today_date.day, 1)

        daily_limit = remaining_money / days_left

    # AFFORDABILITY CHECK
    c.execute(
        '''
        SELECT * FROM afford_checks
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
        ''',

        (session['user_id'],)
    )

    afford_item = c.fetchone()

    afford_message = ""

    if afford_item:

        monthly_savings = balance

        if monthly_savings <= 0:

            afford_message = (
                "⚠️ Increase savings before buying this."
            )

        else:

            months_needed = (
                afford_item['item_price']
                / monthly_savings
            )

            afford_message = (
                f"🛒 You can buy "
                f"{afford_item['item_name']} "
                f"in about "
                f"{months_needed:.1f} month(s)"
            )

    # SPLIT EXPENSES
    c.execute(
        '''
        SELECT * FROM split_expenses
        WHERE user_id=?
        ''',

        (session['user_id'],)
    )

    splits = c.fetchall()

    total_owed = 0

    for split in splits:
        total_owed += split['amount']

    conn.close()

    return render_template(
        'index.html',

        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        suggestion=suggestion,

        food_total=food_total,
        travel_total=travel_total,
        shopping_total=shopping_total,
        salary_total=salary_total,

        budget_warning=budget_warning,
        ai_insight=ai_insight,

        emis=emis,
        emi_alerts=emi_alerts,

        goals=goals,
        goal_insights=goal_insights,

        daily_limit=daily_limit,

        afford_message=afford_message,

        splits=splits,
        total_owed=total_owed
    )



# ADD TRANSACTION


@app.route('/add', methods=['POST'])
def add():

    amount = request.form.get('amount')
    category = request.form.get('category')
    type = request.form.get('type')

    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    c.execute(
        '''
        INSERT INTO transactions
        (amount, category, type, user_id)

        VALUES (?, ?, ?, ?)
        ''',

        (
            float(amount),
            category,
            type,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/')



# ADD EMI

@app.route('/add_emi', methods=['POST'])
def add_emi():

    name = request.form.get('name')
    amount = request.form.get('amount')
    due_date = request.form.get('due_date')

    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    c.execute(
        '''
        INSERT INTO emis
        (name, amount, due_date, user_id)

        VALUES (?, ?, ?, ?)
        ''',

        (
            name,
            amount,
            due_date,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/')


# ADD GOAL


@app.route('/add_goal', methods=['POST'])
def add_goal():

    goal_name = request.form.get('goal_name')
    target_amount = request.form.get('target_amount')
    target_date = request.form.get('target_date')

    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    c.execute(
        '''
        INSERT INTO savings_goals
        (goal_name, target_amount, target_date, user_id)

        VALUES (?, ?, ?, ?)
        ''',

        (
            goal_name,
            target_amount,
            target_date,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/')

# SET MONTHLY BUDGET

@app.route('/set_budget', methods=['POST'])
def set_budget():

    monthly_budget = request.form.get('monthly_budget')

    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    c.execute(
        '''
        INSERT INTO student_profile
        (monthly_budget, user_id)

        VALUES (?, ?)
        ''',

        (
            monthly_budget,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/')


# AFFORDABILITY CHECK

@app.route('/check_afford', methods=['POST'])
def check_afford():

    item_name = request.form.get('item_name')
    item_price = request.form.get('item_price')

    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    c.execute(
        '''
        INSERT INTO afford_checks
        (item_name, item_price, user_id)

        VALUES (?, ?, ?)
        ''',

        (
            item_name,
            item_price,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/')


# SPLIT EXPENSES

@app.route('/add_split', methods=['POST'])
def add_split():

    friend_name = request.form.get('friend_name')
    amount = request.form.get('amount')
    description = request.form.get('description')

    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    c.execute(
        '''
        INSERT INTO split_expenses
        (friend_name, amount, description, user_id)

        VALUES (?, ?, ?, ?)
        ''',

        (
            friend_name,
            amount,
            description,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/')

# LOGIN


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('finance.db')
        conn.row_factory = sqlite3.Row

        c = conn.cursor()

        c.execute(
            '''
            SELECT * FROM users
            WHERE username=? AND password=?
            ''',

            (
                username,
                password
            )
        )

        user = c.fetchone()

        conn.close()

        if user:

            session['user_id'] = user['id']

            return redirect('/')

        return "Invalid Login"

    return render_template('login.html')



# SIGNUP


@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('finance.db')
        c = conn.cursor()

        c.execute(
            '''
            INSERT INTO users
            (username, password)

            VALUES (?, ?)
            ''',

            (
                username,
                password
            )
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')


# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# =========================
# DELETE TRANSACTION
# =========================

@app.route('/delete/<int:id>')
def delete(id):

    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    c.execute(
        '''
        DELETE FROM transactions
        WHERE id=? AND user_id=?
        ''',

        (
            id,
            session['user_id']
        )
    )

    conn.commit()
    conn.close()

    return redirect('/')


app.run(debug=True)