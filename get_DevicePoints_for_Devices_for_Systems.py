#
#   This is a Python script to call the myUplink API which is protected by OAuth2 authentication
#   The necessary OAuth2 Token must have already been allocated and saved to a file called
#   .NIBE_Uplink_API_Token.json in the user's home directory, e.g. using request_token.py
#
#   For more information see https://www.marshflattsfarm.org.uk/wordpress/?page_id=5235
#
#   Usage:
#       python3  get_DevicePoints_for_Devices_for_Systems.py
#
#   Pre-requisites:
#     - A suitable OAuth2 Token must have already been allocated and saved to file
#
from os import path
from json import dump, load
from requests_oauthlib import OAuth2Session

HTTP_STATUS_OK = 200

#   The name of the file used to store the Token needs to be visible within the token_saver() function,
#   so make it a Global Variable
home_dir = path.expanduser('~')
token_filename= home_dir + '/.myUplink_API_Token.json'

#   Define a function that will be automatically called to save a new Token when it is refreshed
def token_saver(token):
    with open(token_filename, 'w') as token_file:
        dump(token, token_file)

#   Edit-in your own client_id and client_secret strings below
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

#   The Swagger API docs provide this example of the expected JSON output
#
#   {
#     "page": 0,
#     "itemsPerPage": 0,
#     "numItems": 0,
#     "systems": [
#       {
#         "systemId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
#         "name": "string",
#         "securityLevel": "admin",
#         "hasAlarm": true,
#         "country": "string",
#         "devices": [
#           {
#             "id": "string",
#             "connectionState": "Disconnected",
#             "currentFwVersion": "string",
#             "product": {
#               "serialNumber": "string",
#               "name": "string"
#             }
#           }
#         ]
#       }
#     ]
#   }

#   The array of Systems is tagged as 'systems' in the JSON output
systems = response.json()['systems']

for system in systems:
    system_id = system['systemId']
    print('System Id:  ' +  str(system_id))

    #   It's the Devices associated with the Systems which have the DataPoints associated with them
    #   There can be more than one Device per System so they're in a JSON array
    devices = system['devices']

    for device in devices:
        device_id = device['id']
        print('\tDevice Id:  ' +  str(device_id))
   
        #   Call the myUplink API - Get the list of DataPoints for this Device
        #   Documentation for this API call is at: https://api.myuplink.com/swagger/index.html
        response = myuplink.get('https://api.myuplink.com/v2/devices/' + str(device_id) + '/points')
        if response.status_code != HTTP_STATUS_OK:
            print('HTTP Status: ' + str(response.status_code))
            print(response.text)
            raise SystemExit('API call not successful')
    
        #   The Swagger API docs provide this example of the expected JSON output
        #
        #   [
        #     {
        #       "category": "string",
        #       "parameterId": "string",
        #       "parameterName": "string",
        #       "parameterUnit": "string",
        #       "writable": true,
        #       "timestamp": "2023-12-23T16:36:42.437Z",
        #       "value": 0,
        #       "strVal": "string",
        #       "smartHomeCategories": [
        #         "string"
        #       ],
        #       "minValue": 0,
        #       "maxValue": 0,
        #       "stepValue": 0,
        #       "enumValues": [
        #         {
        #           "value": "string",
        #           "text": "string",
        #           "icon": "string"
        #         }
        #       ],
        #       "scaleValue": "string",
        #       "zoneId": "string"
        #     }
        #   ]

        #   The JSON output is simply an array of DataPoint objects
        data_points = response.json()

        for data_point in data_points:
            parameter_id = data_point['parameterId']
            parameter_category = data_point['category']
            parameter_name = data_point['parameterName']
            parameter_unit = data_point['parameterUnit']
            parameter_value = data_point['value']
            print('\t\tParameter Id:              ' + str(parameter_id))
            print('\t\t\tCategory:                ' + str(parameter_category))
            print('\t\t\tParameter Name:          ' + str(parameter_name))
            print('\t\t\tParameter Unit:          ' + str(parameter_unit))
            print('\t\t\tParameter Value:         ' + str(parameter_value))
