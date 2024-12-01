#
#   This is a Python script to call the myUplink API (protected by OAuth2 authentication),
#   retrieve DataPoints for the connected Systems & Devices, then publish the DataPoints
#   as MQTT Messages (one Message for the Value, another for the Unit).
#
#   MQTT Messages are published to Topics named like:
#       myuplink/[system_id]/[parameter_id]/value
#       myuplink/[system_id]/[parameter_id]/unit
#
#   The MQTT Server is assumed to require Username & Password authentication.
#
#   Usage:
#       python3  myUplink2MQTT.py
#
#   Pre-requisites:
#     - A suitable OAuth2 Token must have already been allocated and saved to file
#
from os import path
from json import dump, load
from requests_oauthlib import OAuth2Session
import paho.mqtt.client as mqtt

#    Print debug messages?
DEBUG = False
#   Numeric code to expect for a successful HTTP transaction
HTTP_STATUS_OK = 200
#   The hostname or IPv4 address of the MQTT Broker
MQTT_BROKER = 'Replace this with your MQTT server info'
#   The MQTT port number 
MQTT_PORT = 1883
#   The MQTT username
MQTT_USER = 'Replace this with your MQTT username'
#   The MQTT password
MQTT_PASSWORD = 'Replace this with your MQTT password'
#   The MQTT client id
MQTT_CLIENT = 'myUplink2MQTT'

#   The name of the file used to store the Token needs to be visible within the token_saver() function,
#   so make it a Global Variable
home_dir = path.expanduser('~')
token_filename= home_dir + '/.myUplink_API_Token.json'

#   Define a function that will be automatically called to save a new Oauth2 Token when it is refreshed
def token_saver(token):
    with open(token_filename, 'w') as token_file:
        dump(token, token_file)

#   Define a function that will be automatically called when the MQTT client Connects
def on_connect(client, userdata, flags, rc):
    if (DEBUG):
       print('Connected to MQTT server with return code ' + str(rc))

#   Open the connection to the MQTT server
mqtt_client = mqtt.Client(MQTT_CLIENT)
mqtt_client.on_connect = on_connect
#   Comment-out the next line if an Anonymous connection to the MQTT server is acceptable
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.loop_start()

#   Specify the client_id and client_secret strings for the myUplink 'Application'
client_id = 'Replace this with the Identifier issued when your Application was registered' # (36 hex digits)
client_secret = 'Replace this with the Secret issued when your Application was registered' # (32 characters)

token_url = 'https://api.myuplink.com/oauth/token'

#   Read the previously-saved Token from file
with open(token_filename, 'r') as token_file:
    token = load(token_file)

#   Specify the list of extra arguments to include when refreshing a Token
extra_args = {'client_id': client_id, 'client_secret': client_secret}

#   Instantiate an OAuth2Session object (a subclass of Requests.Session) that will be used to query the API
#     - The default Client is of type WebApplicationClient, which is what we want; no need to specify that
#     - The 'client_id' was allocated when the Application was Registered
#     - The 'token' was allocated previously; read-in from a file
#     - The 'auto_refresh_url' says what URL to call to obtain a new Access Token using the Refresh Token
#     - The 'auto_refresh_kwargs' specifies which additional arguments need to be passed when refreshing a Token
#     - The 'token_updater' is the function that will persist the new Token whenever it is refreshed
myuplink = OAuth2Session(client_id=client_id, token=token, auto_refresh_url=token_url, auto_refresh_kwargs=extra_args, token_updater=token_saver)

#   Call the myUplink API - Get a list of the Systems assigned to the authorized user
#   Documentation for this API call is at: https://api.myuplink.com/swagger/index.html
response = myuplink.get('https://api.myuplink.com/v2/systems/me')
if response.status_code != HTTP_STATUS_OK:
    print('HTTP Status: ' + str(response.status_code))
    print(response.text)
    raise SystemExit('API call not successful')

#   The array of Systems is tagged as 'systems' in the JSON output
systems = response.json()['systems']

for system in systems:
    system_id = system['systemId']

    #   It's the Devices associated with the Systems which have the DataPoints associated with them
    #   There can be more than one Device per System so they're in a JSON array
    devices = system['devices']

    for device in devices:
        device_id = device['id']

        #   Call the myUplink API - Get the list of DataPoints for this Device
        #   Documentation for this API call is at: https://api.myuplink.com/swagger/index.html
        response = myuplink.get('https://api.myuplink.com/v2/devices/' + str(device_id) + '/points')
        if response.status_code != HTTP_STATUS_OK:
            print('HTTP Status: ' + str(response.status_code))
            print(response.text)
            raise SystemExit('API call not successful')

        #   The JSON output is simply an array of DataPoint objects
        data_points = response.json()

        for data_point in data_points:
            category = data_point['category']
            parameter_id = data_point['parameterId']
            parameter_name = data_point['parameterName']
            parameter_unit = data_point['parameterUnit']
            parameter_value = data_point['value']
            parameter_str_value = data_point['strVal']
            if (DEBUG):
                print('\t\t\tCategory:                  ' + str(category))
                print('\t\t\t\tParameter Id:            ' + str(parameter_id))
                print('\t\t\t\tParameter Name:          ' + str(parameter_name))
                print('\t\t\t\tParameter Unit:          ' + str(parameter_unit))
                print('\t\t\t\tParameter Value:         ' + str(parameter_value))
                print('\t\t\t\tParameter Display Value: ' + str(parameter_str_value))

            #   Publish the Value for this DataPoint as an MQTT Message
            topic = 'myuplink/' + str(system_id) + '/' + str(parameter_id) + '/value'
            result = mqtt_client.publish(topic, parameter_value)
            if result.rc != 0:
                print('Error publishing to MQTT Broker: ' + str(result.rc))

            #   Publish the Unit for this DataPoint as an MQTT Message
            topic = 'myuplink/' + str(system_id) + '/' + str(parameter_id) + '/unit'
            result = mqtt_client.publish(topic, parameter_unit)
            if result.rc != 0:
                print('Error publishing to MQTT Broker: ' + str(result.rc))

mqtt_client.loop_stop()
mqtt_client.disconnect()
