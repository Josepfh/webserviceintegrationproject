from flask import jsonify
import hashlib
from datetime import datetime
import secrets
import logging
from pymongo import MongoClient, ASCENDING
import time

#Logging configuration
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.DEBUG)

#Token length for API tokens
TOKEN_LEN = 64

#Database config 
DB_CONFIG = {
    "connection_string": "mongodb+srv://yusufcivan_db_user:NIlK39zt3RuwJW1t@webserviceproject.89cp5rc.mongodb.net/?retryWrites=true&w=majority&appName=WebServiceProject",
    "db_name" : 'webserviceproject',
    "collections" : {
        "user_data": "user_data",
        "loads": "loads",
        "user_load": "user_load",
        "user_pwd": "user_pwd",
        "api_keys": "api_keys"
    } 
}

def connect_to_db():
    #Try to connect to the database
    try:
        client = MongoClient(DB_CONFIG['connection_string'])
        client.server_info()
        db = client[DB_CONFIG['db_name']]
        logging.debug('Connected to Mongo!')
        return client, db
    except Exception as e:
        print('Could not connect to Mongo:',e)
        return None, None

client, db = connect_to_db()
connection_attempts = 1
while not db and connection_attempts < 60:
    client, db = connect_to_db()
    connection_attempts = connection_attempts + 1
    time.sleep(10)

if not db:
    logging.debug("Could not connect to Mongo!\nExiting...")
    exit(-1)

#   Authenticate User Password
#   A function to authenticate a user by their password using salt and SHA512 hashing
#   Parameters:
#           - username # Username of the user.
#           - password # Password of the user.
#   Returns: 
#       A JSON object and a status code.
#       Status codes:
#               - 200 # The user is successfully authenticated and the user data is returned.
#               - 401 # The user is not authenticated and an error message is returned.

def authenticate_user_password(username,password):

    # Make a request to the db with the username that returns a salt, and hash.
    # If the username does not match any records in the database the function returns 401
    try:
        pwd_data = get_pwd_data(username)
    except:
        return error_template("Unauthorized due to invalid username or password."),401
    
    # By the security practices we only store the salted hash of the password not the password itself.
    salt = pwd_data['salt'].encode('utf-8') # Encode the salt which is an arbitrary string
    user_pass_hash = pwd_data['hash'] # The stored 'salted hash' to compare against.
    pass_hash = password_encode(password,salt) # Calculate the 'salted hash' for the given password and retrieved salt.
    
    # Incorrect credentials.
    # 401 is returned.
    if pass_hash != user_pass_hash:
        return error_template("Unauthorized due to invalid username or password."),401

    # Correct credentials
    api_token = generate_api_token() # Generate an api token
    logging.debug('Generated API token: %s', api_token)
    
    user_data = get_user_data(username) # Make another request to the db for all the user info
    user_data = add_token_to_data(user_data,api_token) # Add the token to return to the user.
    add_token_to_db(username,api_token) # Make another request to add the newly generated API token to the token list in the database.
    
    return jsonify(user_data),200

#   Validate API Token
#   A function to validate an API token.
#   Parameters:
#           -   token # API token
#   Returns: 
#       A JSON object and a status code.
#       Status codes:
#               - 200 # The API key is successfully authenticated and the user data for the corresponding user is returned.
#               - 401 # The API key is not authenticated and an error message is returned.

def validate_token(token):
    
    user, valid_token = check_token(token) # Check if the token is valid
    
    # Valid case
    if valid_token:
        user_data = get_user_data(user) # Get the corresponding user data
        user_data = add_token_to_data(user_data,token) # Add the token to the data.
        return jsonify(user_data),200 
    
    #Invalid case
    return error_template("Unauthorized due to invalid username or password."),401

#   Get loads
#   A function to retrieve loads for a user
#   Parameters:
#           -   token # API token
#   Returns: 
#       A JSON object and a status code.
#       Status codes:
#               - 200 # The API key is successfully authenticated and the user loads for the corresponding user is returned.
#               - 401 # The API key is not authenticated and an error message is returned.

def get_loads(token):
    user, valid_token = check_token(token) # Check if the token is valid.

    # Valid case
    if valid_token:
        load_data = get_load_data(user) # Get the load data for the given user.
        return load_data, 200
    
    #Invalid case
    return error_template("Unauthorized due to missing or invalid token and/or API key."),401
    

# ************HELPER FUNCTIONS***************



#   Error Template
#   A function for an error template.
#   Parameters:
#           -   error # Error message
#   Returns: 
#       A JSON object with the correct error message.

def error_template(error):
    return jsonify({
            'error': error
        })

#   Password encode
#   A function to encode a password
#   Parameters:
#           -   password # user password
#           -   salt # the salt for hashing
#   Returns: 
#       512 bits long hex string aka 'salted hash' of the given password and salt.

def password_encode(password, salt):
    password_hash = hashlib.sha512(salt + password.encode('utf-8')).hexdigest()
    return password_hash

#   Generate API Token
#   A function to generate an API token.
#   Returns: 
#       64 bits long and url safe string generated with the secrets library. 

def generate_api_token():
    return secrets.token_urlsafe(TOKEN_LEN)

#   Password encode
#   A function to check an API token
#   Parameters:
#           -   token # API token
#   Returns: 
#       -   string value to indicate the username of the corresponding user.
#       -   boolean value to indicate if the token is valid or not.

def check_token(token) :

    logging.debug('Checking API token: %s', token)
    # Get the corresponding user from the database.
    collection = db[DB_CONFIG['collections']['api_keys']]
    user = collection.find_one({'api_key':token})
    # If the user is found
    if user:
        return user['username'],True 
    # If the user is not found
    return None, False

#   Get user data
#   A function to get user data.
#   Parameters:
#           -   username # username of the user.
#   Returns: 
#       JSON object with the corresponding user data.

def get_user_data(username):

    logging.debug('Getting user data for the user: %s', username)

    # Get user data from the db
    collection = db[DB_CONFIG['collections']['user_data']]
    user_data = collection.find_one({'username':username})
    user_data.pop('_id') # Pop the unique id that's used for db purposes.
    logging.debug('Found user data')
    return user_data

#   Add Token to Data
#   A function to add a token to a dict object
#   Parameters:
#           -   data # dict object with user data
#           -   token # the API token to be added.
#   Returns: 
#       A dict object with the API token as one of the properties.

def add_token_to_data(data,token):
    data['api_token'] = token
    return data

#   Get Load Data
#   A function to retrieve loads for a given user.
#   Parameters:
#           -   username # username of the user.
#   Returns: 
#       An array of dict objects with load data.

def get_load_data(username):

    logging.debug('Getting load data for the user: %s', username)

    # Get load ids that are assigned to this user.
    collection = db[DB_CONFIG['collections']['user_load']]
    load_list = collection.find({'username': username}).sort('sort',ASCENDING)
    load_ids = [load['load_id'] for load in load_list]
    
    # Get loads by load ids and put them in an array.
    collection = db[DB_CONFIG['collections']['loads']]
    loads = []
    for index, id in enumerate(load_ids):
        load = collection.find_one({'id':id})
        load.pop('_id')
        load['sort'] = index + 1
        loads.append(load)
    return loads

#   Add Token to Database
#   A function to add an API key to the database
#   Parameters:
#           -   username # username of the user
#           -   token # API token to be added.
#   Returns: 
#       None

def add_token_to_db(username,token):
    collection = db['api_keys']
    collection.insert_one({'api_key':token,'username':username,'datetime':datetime.now().isoformat()})

#   Get Password Data
#   A function to get the password data for the given user
#   Parameters:
#           -   username # username of the user
#   Returns: 
#       dict object with the users data.

def get_pwd_data(username):
    collection = db[DB_CONFIG['collections']['user_pwd']]
    pwd_data = collection.find_one({'username':username})
    pwd_data.pop('_id') # Pop the unique id that's used for db purposes.
    return pwd_data