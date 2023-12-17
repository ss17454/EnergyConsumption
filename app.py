from flask import Flask, render_template, request, redirect, url_for, session
from flask import Flask, render_template, request, jsonify
import mysql.connector
import re
from flask import Flask, render_template, request
from datetime import datetime
import mysql.connector
import re
from flask import Flask, render_template, request
from datetime import datetime
import mysql.connector
import re
from flask import Flask, render_template
from io import BytesIO
import base64
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)
app.secret_key = 'your_secret_key'
global location_id

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Abcde@99',
    'database': 'SHEMS',
}

# Initialize MySQL connection
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(buffered=True)

# Create users table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL
    )
""")
conn.commit()

@app.route('/')
def index():
   if 'username' in session:
       return 'Logged in as ' + session['username'] + '<br><a href="/logout">Logout</a>'
   #return 'You are not logged in<br><a href="/login">Login</a>'
   return render_template('index.html')


@app.route('/user_dashboard')
def user_dashboard():

    # Assume you have a function to fetch device models from the database
    cursor.execute("""
            SELECT DISTINCT Type FROM DeviceModel 
        """)
    dropdown_values = cursor.fetchall()
    #device_models = get_device_models()
    return render_template('userDashboard.html', dropdown_values=dropdown_values)

@app.route('/get_second_dropdown', methods=['POST'])
def get_second_dropdown():
   # Get the selected value from the first dropdown
   selected_value = request.form['selected_value']


   # Fetch options for the second dropdown based on the selected value
   cursor.execute("""
       SELECT modelnumber FROM devicemodel WHERE type = %s
   """, (selected_value,))
   second_dropdown_values = cursor.fetchall()


   return {'options': second_dropdown_values}

@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
       email = request.form['email']
       password = request.form['password']


       # Check if the input is a valid email address
       if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
           return 'Invalid email address. Please enter a valid email.'


       cursor.execute("""
           SELECT * FROM users WHERE username=%s AND password=%s
       """, (email, password))
       user = cursor.fetchone()


       if not user:
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('login'))


       # Fetch options for the first dropdown
       cursor.execute("""
           SELECT distinct type FROM devicemodel
       """)
       first_dropdown_values = cursor.fetchall()

       cursor.execute(""" SELECT CustomerID FROM Customer WHERE email = %s
        """, (email,))
       cust_ID = cursor.fetchone()

       cursor.executemany("""
            SELECT LocationID, unitNumber, MoveInDate, SquareFootage, City, Street, Zipcode
            FROM serviceLocation
            WHERE CustomerID =  %s
        """, (cust_ID,))
       locations = cursor.fetchall()
    


       cursor.execute("""
           SELECT customerid FROM customer WHERE email=%s
       """, (email,))
       customer_id= cursor.fetchall()

       cursor.execute('''
       SELECT sl.locationid
       FROM servicelocation sl
       JOIN customer c ON sl.customerid = c.customerid
       WHERE c.email = %s ''', (email, ))
       location_ids = [row[0] for row in cursor.fetchall()]



       return render_template('userDashboard.html', first_dropdown_values=first_dropdown_values,locations=locations, location_ids = location_ids, cust_ID = int(cust_ID[0]))


       if user:
           session['username'] = email
           return redirect(url_for('index'))


   return render_template('login.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
   if request.method == 'POST':
       email = request.form['Email']
       password = request.form['password']
       firstName = request.form['firstName']
       lastName = request.form['lastName']
       city = request.form['city']
       street = request.form['street']
       zipCode = request.form['zipCode']


       if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
           return 'Invalid email address format. Please use a valid email address.'


       # Check if the username is already taken
       cursor.execute("""
           SELECT * FROM users WHERE username=%s
       """, (email,))
       existing_user = cursor.fetchone()


       if existing_user:
           return 'Username already taken. Please choose another username.'


       # Insert the new user into the database
       cursor.execute("""
           INSERT INTO users (username, password) VALUES (%s, %s)
       """, (email, password))
       conn.commit()


       # Insert the new user personal information into the database
       cursor.execute("""
           insert into customer(firstName,lastName,city,street,zipCode,email) values  (%s, %s, %s, %s, %s, %s)
       """, (firstName, lastName, city, street, zipCode, email))
       conn.commit()


       return 'Registration successful! <a href="/login">Login</a>'


   return render_template('signup.html')


@app.route('/add_new_device', methods=['POST'])
def add_new_device():
    model_type = request.form['newModelType']
    model_number = request.form['newModelNumber']

    # Insert the new device into the DeviceModel table
    cursor.execute("""
        INSERT INTO DeviceModel (Type, ModelNumber) VALUES (%s, %s)
    """, (model_type, model_number))
    conn.commit()

    return 'Device added successfully!'

@app.route('/location_details', methods=['POST'])
def location_details():
    location_id = request.form['location_id']

    # Fetch details for the selected location
    cursor.execute("""
        SELECT *
        FROM ServiceLocation
        WHERE LocationID = %s
    """, (location_id,))
    location_details = cursor.fetchone()

    # Render a template to display location details
    return render_template('locationDetails.html', location_details=location_details, location_id = location_id)

@app.route('/save_devicetoLocation', methods=['POST'])
def save_devicetoLocation():
   if request.method == 'POST':
       # device_type = request.form['device_type_other']
       # device_model = request.form['device_model_other']
       device_type = request.form['firstDropdown']
       location_id = request.form['location_id']
       model_number = request.form['secondDropdown']


       cursor.execute("""
           SELECT modelid FROM devicemodel WHERE ModelNumber = %s
       """, (model_number,))
       model_id = cursor.fetchone()


       if not model_id:
           return 'Error: Selected model number not found.'
      
       model_id = model_id[0]


       # Save to MySQL database


       # cursor.execute("""
       #      INSERT INTO devicemodel (type, modelnumber) VALUES (%s, %s)""", (device_type, device_model))
       # conn.commit()


       cursor.execute("""
            INSERT INTO EnrolledDevice (LocationID, ModelID, DeviceName) VALUES (%s, %s, %s)""", (location_id, model_id, device_type))
       conn.commit()
       return 'Device information saved successfully to location!<a href="/login">Login</a>'
   

   # Route for adding a new service location
@app.route('/add_new_service_location<int:cust_ID>', methods=['GET', 'POST'])
def add_new_service_location(cust_ID):
   if request.method == 'POST':
       # Get values from the form
       print("inside this")
       unit_number = request.form.get('unitNumber')
       move_in_date = request.form.get('moveInDate')
       square_footage = request.form.get('squareFootage')
       bedrooms = request.form.get('bedrooms')
       occupants = request.form.get('occupants')
       city = request.form.get('city')
       street = request.form.get('street')
       zip_code = request.form.get('zipCode')


       # Add the new service location to the database
       success = add_new_service_location_db(cust_ID,unit_number, move_in_date, square_footage, bedrooms, occupants, city, street, zip_code)


       if success:
           return 'Location added successfully! <a href="/login">Login</a>'
       
       else:
           return "Failed to add the new service location. Please try again."


def add_new_service_location_db(customer_id,unit_number, move_in_date, square_footage, bedrooms, occupants, city, street, zip_code):
   try:
       print("here!")
       # Replace 'your_table_name' with the actual name of your service location table
       cursor.execute("""
       INSERT INTO servicelocation (customerid, unitnumber, MoveInDate, SquareFootage, Bedrooms, Occupants, City, Street, ZipCode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
           (customer_id, unit_number, move_in_date, square_footage, bedrooms, occupants, city, street, zip_code))


       conn.commit()
      


       return True
   except Exception as e:
       print(f"Error adding new service location: {e}")
       return False

   




@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))



@app.route('/save_device', methods=['POST'])
def save_device():
   if request.method == 'POST':
       device_type = request.form['firstDropdown']
       location_id = request.form['location_id']
       model_number = request.form['secondDropdown']

       cursor.execute("""
           SELECT modelid FROM devicemodel WHERE ModelNumber = %s
       """, (model_number,))
       model_id = cursor.fetchone()


       if not model_id:
           return 'Error: Selected model number not found.'
       model_id = model_id[0]

       cursor.execute("""
            INSERT INTO EnrolledDevice (LocationID, ModelID, DeviceName) VALUES (%s, %s, %s)""", (location_id, model_id, device_type))
       conn.commit()

       return 'Device information saved successfully to location!<a href="/login">Login</a>'

@app.route('/daily_energy_consumption/<int:location_id>', methods=['GET', 'POST'])
def daily_energy_consumption(location_id):
  if request.method == 'POST':
      selected_date = request.form['selected_date']
  else:
      # Set a default date or fetch it from the database based on your requirements
      selected_date = datetime.now().strftime('%Y-%m-%d')

  return render_template('dailyEnergyConsumption.html', location_id=location_id, selected_date=selected_date)

@app.route('/get_daily_energy_price_consumption', methods=['POST'])
def get_daily_energy_price_consumption():
  location_id = request.json.get('location_id')
  selected_date = request.json.get('selected_date')
   # Fetch hourly energy prices from the database based on location_id and selected_date
  cursor.execute("""
       SELECT HOUR(TimeStamp) AS Hour, SUM(EventData.Value * EnergyPrice.HourlyRate) AS TotalPrice
       FROM EventData
       JOIN EnrolledDevice ON EventData.DeviceID = EnrolledDevice.DeviceID
       JOIN ServiceLocation ON EnrolledDevice.LocationID = ServiceLocation.LocationID
       JOIN EnergyPrice ON ServiceLocation.LocationID = EnergyPrice.LocationID
       WHERE ServiceLocation.LocationID = %s AND DATE(EventData.TimeStamp) = %s
       GROUP BY HOUR(TimeStamp)
   """, (location_id, selected_date))
  energy_data = cursor.fetchall()


  labels = [entry[0] for entry in energy_data]
  values = [entry[1] for entry in energy_data]
  print("lables : ", labels)
  print(values)
  return jsonify({'labels': labels, 'values': values})




# @app.route('/daily_energy_consumption/<int:location_id>')
# def daily_energy_consumption(location_id):
#     return render_template('dailyEnergyConsumption.html', location_id=location_id, selected_date='2023-01-01')




@app.route('/daily_energy_price_consumption/<int:location_id>', methods=['GET', 'POST'])
def daily_energy_price_consumption(location_id):
  if request.method == 'POST':
      print('here!')
      selected_date = request.form['selected_date']
      print(selected_date)
  else:
      # Set a default date or fetch it from the database based on your requirements
      selected_date = datetime.now().strftime('%Y-%m-%d')


  return render_template('energyPrices.html', location_id=location_id, selected_date=selected_date)



@app.route('/get_daily_energy_consumption', methods=['POST'])
def get_daily_energy_consumption():
  location_id = request.json.get('location_id')
  selected_date = request.json.get('selected_date')


  cursor.execute("""
      SELECT DeviceID, DATE(Timestamp) AS labels, SUM(Value)
FROM EventData
WHERE DeviceID IN (
   SELECT DeviceID
   FROM EnrolledDevice
   WHERE LocationID = %s
) AND EventLabel = 'energy Use'
   AND DATE(Timestamp) = %s
GROUP BY DeviceID, DATE(Timestamp);
  """, (location_id, selected_date))

  energy_data = cursor.fetchall()

  # Prepare data for plotting
  labels = [str(entry[1]) for entry in energy_data]
  values = [int(entry[2]) for entry in energy_data]
  print("lables : ", labels)
  print(values)
  return jsonify({'labels': labels, 'values': values})


@app.route('/total_energy_consumption/<int:location_id>', methods=['GET', 'POST'])
def total_energy_consumption(location_id):
  if request.method == 'POST':
      selected_date = request.form['selected_date']
  else:
      # Set a default date or fetch it from the database based on your requirements
      selected_date = datetime.now().strftime('%Y-%m-%d')

  return render_template('totalEnergyConsumption.html', location_id=location_id, selected_date=selected_date)


@app.route('/get_total_energy_consumption', methods=['POST'])
def get_total_energy_consumption():
  location_id = request.json.get('location_id')
  selected_date = request.json.get('selected_date')


  cursor.execute("""
SELECT
    DATE_FORMAT(EventData.Timestamp, '%Y-%m-%d %H:00:00') AS Hour,
    SUM(EventData.Value) AS TotalEnergyConsumption
FROM EventData
JOIN EnrolledDevice ON EventData.DeviceID = EnrolledDevice.DeviceID
WHERE EventData.EventLabel = 'energy use'
AND EnrolledDevice.LocationID = %s  -- Replace with your specific location ID
AND DATE(EventData.Timestamp) = %s  -- Replace with your specific date
GROUP BY DATE_FORMAT(EventData.Timestamp, '%Y-%m-%d %H:00:00');

  """, (location_id, selected_date))

  energy_data = cursor.fetchall()

  # Prepare data for plotting
  labels = [str(entry[0]) for entry in energy_data]
  values = [int(entry[1]) for entry in energy_data]
  print("lables : ", labels)
  print(values)
  return jsonify({'labels': labels, 'values': values})


@app.route('/yearly_energy_consumption/<int:location_id>', methods=['GET', 'POST'])
def yearly_energy_consumption(location_id):
  if request.method == 'POST':
      selected_date = request.form['selected_date']
  else:
      # Set a default date or fetch it from the database based on your requirements
      selected_date = datetime.now().strftime('%Y-%m-%d')

  return render_template('yearlyEnergyConsumption.html', location_id=location_id, selected_date=selected_date)


@app.route('/get_yearly_energy_consumption', methods=['POST'])
def get_yearly_energy_consumption():
  location_id = request.json.get('location_id')
  selected_date = request.json.get('selected_date')


  cursor.execute("""
SELECT
    YEAR(EventData.Timestamp) AS Year,
    SUM(EventData.Value) AS TotalEnergyConsumption
FROM EventData
JOIN EnrolledDevice ON EventData.DeviceID = EnrolledDevice.DeviceID
WHERE EventData.EventLabel = 'energy use'
AND EnrolledDevice.LocationID = %s -- Replace with the desired location ID
AND YEAR(EventData.Timestamp) >= %s -- Replace with the selected year
GROUP BY YEAR(EventData.Timestamp)
ORDER BY YEAR(EventData.Timestamp);

  """, (location_id, selected_date))

  energy_data = cursor.fetchall()

  # Prepare data for plotting
  labels = [str(entry[0]) for entry in energy_data]
  values = [int(entry[1]) for entry in energy_data]
  print("lables : ", labels)
  print(values)
  return jsonify({'labels': labels, 'values': values})


@app.route('/hourly_energy_price/<int:location_id>', methods=['GET', 'POST'])
def hourly_energy_price(location_id):
  if request.method == 'POST':
      selected_date = request.form['selected_date']
  else:
      # Set a default date or fetch it from the database based on your requirements
      selected_date = datetime.now().strftime('%Y-%m-%d')

  return render_template('hourlyEnergyPriceChange.html', location_id=location_id, selected_date=selected_date)


@app.route('/get_hourly_energy_price', methods=['POST'])
def get_hourly_energy_price():
  location_id = request.json.get('location_id')
  selected_date = request.json.get('selected_date')


  cursor.execute("""
    SELECT
    DATE(EnergyPrice.EffectiveDate) AS Date,
    MAX(EnergyPrice.HourlyRate) AS MaxHourlyRate
FROM EnergyPrice
WHERE EnergyPrice.LocationID = %s -- Replace with the desired location ID
AND EnergyPrice.EffectiveDate >= %s -- Replace with the selected date in 'YYYY-MM-DD' format
AND EnergyPrice.EffectiveDate < DATE_ADD(%s, INTERVAL 8 DAY) -- Selects up to 7 days after the selected date
GROUP BY DATE(EnergyPrice.EffectiveDate)
ORDER BY DATE(EnergyPrice.EffectiveDate);
  """, (location_id, selected_date, selected_date))

  energy_data = cursor.fetchall()

  # Prepare data for plotting
  labels = [str(entry[0]) for entry in energy_data]
  values = [int(entry[1]) for entry in energy_data]
  print("lables : ", labels)
  print(values)
  return jsonify({'labels': labels, 'values': values})


@app.route('/delete_location', methods=['POST'])
def delete_location():
    location_id = request.form['deleteLocationId']
    
    try:
        # Replace the following SQL query with the correct one based on your schema
        cursor.execute("DELETE FROM ServiceLocation WHERE LocationID = %s", (location_id,))
        conn.commit()
        # You might want to add flash messages here for success or failure
        return redirect(url_for('login'))
    except mysql.connector.Error as err:
        # Handle the error (e.g., log it, flash an error message)
        print(f"Error: {err}")
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
