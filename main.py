
from flask import Flask, request, session
from flask_socketio import send, SocketIO, emit
import json
from uuid import uuid4
import math

app = Flask(__name__)
app.config["SECRET_KEY"] = "bllleee"
socketio = SocketIO(app)

connHW, connApp = (None, None)
data_variables = {
    "width": 0,
    "radius": 0,
    "height": 0,
    "length": 0,
    "Tank1dist": 0,
    "Tank2dist": 0,
    "PumpState": None,
    "pump_control": None,
    "solenoidAsize": 0,
    "solenoidBsize": 0,
    "solenoidA": None,
    "solenoidB": None
}

def generate_unique_id(length):
    return str(uuid4()) #generate a unique identifyer for each connection
   

#Websocket connect
@socketio.on('connect')
def handle_connect():
    token = request.args.get('token') #get token from url to ientify user as HW or app
    if token == 'Hardware':
        session['Hardware'] = request.sid
    elif token == 'app':
        session['app'] = request.sid
    else: print('Error!!!unknown connection')
        # map the token of the HW/app to its connection id for asy access later
   
#Websocket disconnect
@socketio.on('disconnect')
def handle_disconnect():
    token = request.args.get('token') #get token from url to ientify user as HW or app
    if token in session:
        session.pop(token) #delete connection id

#update from app    
@socketio.on("message")
def handle_message(msg):
    data = json.loads(msg) # retrieve the recieved json message data
    if 'TankSize' in data:  # check if it contains the require details
        msg1 = data['TankSize']
        msg2 = data['Tank_index']
        update_session_with_tank_size(msg1,msg2)
        
       
    elif 'PumpState' in data:
        msgPump = data['PumpState']
        session['PumpState'] = msgPump
        
    elif 'TankState' in data:
        msgTank = data['TankState']
        msgT2 = data['Tank_index']
        
        session ['Tank ' + msgT2 + ' size'] = msgTank
    
    elif 'Tank_index' in data:
        tankIndex = data['Tank_index']
        tankState = data['TankState']
        session['Tank ' + tankIndex + ' state'] = tankState
#update from hardware
    elif 'Data' in data:
        msg1 = data['Data']
        PumpStatus = msg1['Pump Status']
        Tank1 = msg1['Tank1']
        Tank2 = msg1['Tank2']
    
        session['HardwareData'] = {
            'PumpStatus':PumpStatus,
            'Tank1': Tank1, 
            'Tank2': Tank2
        }

    fetch_data()   
    handle_sendToApp()
    handle_sendToTank()

#send to app
def handle_sendToApp():
    fetch_data()
    #calculate volume
    if data_variables["width"] == 0:
        volume = calculate_volume_cylinder(data_variables["radius"], data_variables["height"], data_variables["Tank1dist"], data_variables["Tank2dist"])
    else:   
        volume = calculate_volume_rectangular(data_variables["length"],data_variables["width"], data_variables["height"], data_variables["Tank1dist"],data_variables["Tank2dist"])
               
    val = [volume[0],volume[1]]
            

    emit('message', data_variables["PumpState"], room = connApp)
    emit('message', val, room = connApp) 

#send to tank
def handle_sendToTank():
    fetch_data()
    val = {
        'pump_control': data_variables["pump_control"],
        'solenoidAsize': data_variables["solenoidAsize"],
        'solenoidBsize': data_variables["solenoidBsize"],
        'solenoidA': data_variables["solenoidA"],
        'solenoidB': data_variables["solenoidB"],
    }
    
    emit('message', val, room = connHW)

def update_session_with_tank_size(data, tank_index):
    radius = data["radius"]
    height = data["height"]
    width = data["width"]
    length = data["length"]

    tank_sizes = 'Tank ' + tank_index + ' dimension'
    session[tank_sizes] = {'radius': radius, 'height': height, 'width': width, 'length': length}
   

def fetch_data():
    #fetch connectionID
    global connHW, connApp
    connHW = session.get('Hardware')
    connApp = session.get('app')

    #fetch data from session
    tank_sizes = session.get('Tank 1 dimension')
    for key, value in tank_sizes.items():
        if key in data_variables:
            data_variables[key] = value
        if key is 'height':
            data_variables['solenoidAsize'] = value

    tank_sizes_2 = session.get('Tank 2 dimension')
    for key, value in tank_sizes_2.items():
        if key in data_variables:
            data_variables[key] = value
        if key is 'height':
            data_variables['solenoidBsize'] = value

    hardware_data = session.get('HardwareData')
    for key, value in hardware_data.items():
        if key in data_variables:
            data_variables[key] = value

    pump_control = session.get('PumpState')
    if pump_control is not None:
        for key, value in pump_control.items():
            if key in data_variables:
                data_variables[key] = value

    #fetch ON/OFF instructon for tanks. Addd more for more tanks
    solenoidA = session.get('Tank 1 state')
    data_variables['solenoidA'] = solenoidA
    solenoidB = session.get('Tank 2 state')
    data_variables['solenoidB'] = solenoidB

# Function to calculate the volume of a cylindrical tank
def calculate_volume_cylinder(radius, height, Tank1dist,Tank2dist):
    volumeOfTank = math.pi * radius * radius * height
    volumeLeft1 = math.pi * Tank1dist * radius * radius
    volumeLeft2 = math.pi * Tank2dist * radius * radius
            
    VolumeFilled1 = (volumeOfTank - volumeLeft1)/volumeOfTank
    VolumeFilled2 = (volumeOfTank - volumeLeft2)/volumeOfTank

    return [VolumeFilled1, VolumeFilled2]

# Function to calculate the volume of a rectangular tank
def calculate_volume_rectangular(length, width, height, Tank1dist, Tank2dist):
    volumeOfTank = length * width * height
    volumeLeft1 = Tank1dist * width * length
    volumeLeft2 = Tank2dist * width * length
            
    VolumeFilled1 = ((volumeOfTank - volumeLeft1)/volumeOfTank)
    VolumeFilled2 = ((volumeOfTank - volumeLeft2)/volumeOfTank)
            
    return [VolumeFilled1,VolumeFilled2]  
            

if __name__ == "__main__":
    socketio.run(app,debug = False)