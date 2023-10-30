from flask import Flask, request, jsonify
import mysql.connector
import requests
import secrets
import uuid
import json

app = Flask(__name__)

# Configuration for MySQL
mysql_host = 'localhost'
mysql_user = 'anagha'
mysql_password = 'anagha123'
mysql_database = 'oauth'

# MySQL Connection
mysql = mysql.connector.connect(
    host='localhost',
    user='anagha',
    password='anagha123',
    database='oauth'
)

# Dictionary to store client information (client_id, client_secret, etc.)
clients = {}

# Dictionary to store access tokens
access_tokens = {}


@app.route('/register', methods=['POST'])
def register_client():
    data = request.get_json()
    client_id = str(uuid.uuid4())  # Generate a random client_id
    client_secret = str(uuid.uuid4())  # Generate a random client_secret
    grant_type = data.get('grant_type')

    # Store the client information in the clients dictionary
    clients[client_id] = {'client_secret': client_secret, 'grant_type': grant_type}

    cursor = mysql.cursor()
    cursor.execute("INSERT INTO clients (client_id, client_secret,grant_type) VALUES (%s, %s,%s)", (client_id, client_secret,grant_type))
    mysql.commit()
    cursor.close()
    return jsonify({'client_id': client_id, 'client_secret': client_secret})


# Function to generate and save an access token
def generate_access_token(client_id, grant_type):
    if grant_type !=grant_type:
        return None

    # Generate a random access token
    access_token = secrets.token_urlsafe(32)

    try:
        cur = mysql.cursor()
        # Insert the access token into the database
        query = "INSERT INTO oauth_token(client_id, access_token) VALUES (%s, %s)"
        values = (client_id, access_token)
        cur.execute(query, values)
        mysql.commit()
        cur.close()
    except Exception as e:
        # Handle database errors
        print("Error saving access token to the database:", str(e))
        return None

    return access_token 

@app.route('/get_token', methods=['POST'])
def get_token():
    data = request.get_json()
    client_id = data.get('client_id')
    grant_type = data.get('grant_type')

    if client_id not in clients:
        return jsonify({'error': 'Invalid client_id'}), 401

    if grant_type != grant_type:
        return jsonify({'error': 'Invalid grant_type'}), 401

    # Generate and save an access token
    access_token = generate_access_token(client_id, grant_type)

    if access_token:
        return jsonify({'access_token': access_token})
    else:
        return jsonify({'error': 'Access token generation and storage failed'}), 500


#     # Your existing code for request handling here...
@app.route('/execute_request', methods=['POST'])
def execute_request():
    data = request.get_json()
    url = data.get('url')
    verb_type = data.get('verb_type')
    json_data = json.dumps(data.get('json_data'))
    access_token = data.get('access_token')  # Get the access_token from the request

    # Check if the HTTP verb type is valid (GET, POST, PUT, DELETE)
    if verb_type not in ['GET', 'POST', 'PUT', 'DELETE']:
        return jsonify({'error': 'Invalid HTTP verb type'}), 400

    # Verify the access_token
    if not verify_access_token(access_token):
        return jsonify({'error': 'Invalid access_token'}), 401

    cur = mysql.cursor()

    # Example SQL Query (You'll need to customize this query based on your needs)
    query = "INSERT INTO access (url, verb_type, json_data, access_token) VALUES (%s, %s, %s, %s)"
    values = (url, verb_type, json_data, access_token)

    try:
        cur.execute(query, values)
        mysql.commit()

        # Additional logic to handle the database response
        if cur.rowcount > 0:
            # The database operation was successful
            return jsonify({'message': 'Request saved to the database'}), 200
        else:
            # The database operation did not affect any rows (no data inserted)
            return jsonify({'error': 'Database operation had no effect'}), 400

    except Exception as e:
        return jsonify({'error': 'Database error', 'message': str(e)}), 500
    finally:
        cur.close()

def verify_access_token(access_token):
    try:
        cur = mysql.cursor()
        query = "SELECT access_token FROM oauth_token WHERE access_token = %s"
        cur.execute(query, (access_token,))
        result = cur.fetchone()
        cur.close()
        return result is not None  # True if a match was found, False if not
    except Exception as e:
        return False  # An error occurred



if __name__ == '__main__':
    app.run(debug=True)