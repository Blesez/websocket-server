
from flask import Flask, request, session
from flask_socketio import send, SocketIO, emit
import json
from uuid import uuid4

app = Flask(__name__)
app.config["SECRET_KEY"] = "bllleee"
socketio = SocketIO(app)


def generate_unique_id(length):
    return str(uuid4()) #generate a uniqnpue identifyer for each connection
   
if __name__ == "__main__":
    socketio.run(app,debug = True)

#Websocket connect
@socketio.on('connect')
def handle_connect():
    token = request.args.get('token') #get token from url to ientify user as HW or app
    session[token] = request.sid # map the token of the HW/app to its connection id for asy access later
   
#Websocket disconnect
@socketio.on('disconnect')
def handle_disconnect():
    token = request.args.get('token') #get token from url to ientify user as HW or app
    session.pop(token, None) #delete connection id

#update from app    
@socketio.on("message")
def handle_message(msg):
    data = json.loads(msg) # retrieve the recieved json message data
    if 'TankSize' in data:  # check if it contains the require details
        msg1 = data['TankSize']
        msg2 = data['Tank_index']
        
        r = msg1["radius"]
        h = msg1["height"] 
        w = msg1["width"]
        l = msg1['length']
        
        radius = r.lower()
        height = h.lower()
        width = w.lower()  
        length = l.lower()  
        
        TankSizes = 'Tank ' + msg2 + ' dimension'
        session[TankSizes] = {'radius': radius, 'height': height, 'width': width, 'length': length} #save to session
    
    elif 'PumpState' in data:
        msgPump = data['PumpState']
        session['PumpState'] = {msgPump}
        
    elif 'TankState' in data:
        msgTank = data['TankState']
        msgT2 = data['Tank_index']
        
        session ['Tank ' + msgT2 + ' size'] = {msgTank}
    
    elif 'Tank_index' in data:
        tankIndex = data['Tank_index']
        tankState = data['TankState']
        session['Tank' + tankIndex + 'state'] = {tankState}
#update from hardware
    elif 'Data' in data:
        msg1 = data['Data']
        
        PumpControl = msg1['Pump Status']
        Tank01 = msg1['Tank1']
        Tank02 = msg1['Tank2']
        
        PumpStatus = PumpControl.lower()
        Tank1 = Tank01.lower()
        Tank2 = Tank02.lower()
        
        session['HardwareData'] = {'PumpStatus':PumpStatus, 'Tank1': Tank1, 'Tank2': Tank2}
        
#send to app
@socketio.on("sendToApp")
def handle_sendToApp():
    #fetch connectionID
    connHW = session.get('Hardware')
    connApp = session.get('app')
    #fetch data from session
    tankSizes = session.get('TankSizes')
    radius= tankSizes.get('radius')
    height = tankSizes.get('height')
    width = tankSizes.get('width')
    length = tankSizes.get('length')
    Tank1dist = session.get('Tank1')
    Tank2dist = session.get('Tank2')
    PumpState = session.get('pumpStatus')
    
     #calculate volume
    if width == 0:
            volumeOfTank = 3.142 * radius * radius * height
            volumeLeft1 = 3.142* Tank1dist * radius * radius
            volumeLeft2 = 3.142 * Tank2dist * radius * radius
            
            VolumeFilled1 = (volumeOfTank - volumeLeft1)/volumeOfTank
            VolumeFilled2 = (volumeOfTank - volumeLeft2)/volumeOfTank
            
            val = [VolumeFilled1,VolumeFilled2]
            
            emit('post_message', PumpState, room = connApp)
            emit('post_message', val, room = connApp)

    elif radius == 0:
            volumeOfTank = length * width * height
            volumeLeft1 = Tank1dist * width * length
            volumeLeft2 = Tank2dist * width * length
            
            VolumeFilled1 = ((volumeOfTank - volumeLeft1)/volumeOfTank)
            VolumeFilled2 = ((volumeOfTank - volumeLeft2)/volumeOfTank)
            
            val = [VolumeFilled1,VolumeFilled2]  
            emit('post_message', PumpState, room = connApp)
            emit('post_message', val, room = connApp) 

#send to tank
@socketio.on("sendToTank")
def handle_sendToTank():
    #fetch connectionID
    connHW = session.get('Hardware')
    connApp = session.get('app')
    pump_control = session.get('PumpState')
    #get height of each tank. Add more for more tanks
    tank1Sizes = session.get('Tank1dimension')
    solenoidAsize = tank1Sizes.get('height')
    tank2Sizes = session.get('Tank2dimension')
    solenoidBsize = tank2Sizes.get('height')
    #fetch ON/OFF instructon for tanks. Addd more for more tanks
    solenoidA = session.get('Tank1state')
    solenoidB = session.get('Tank2state')
    
    val = {
        'pump_control': pump_control,
        'solenoidAsize': solenoidAsize,
        'solenoidBsize': solenoidBsize,
        'solenoidA': solenoidA,
        'solenoidB': solenoidB,
    }
    
    emit('post_message', val, room = connHW)