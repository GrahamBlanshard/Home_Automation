GaragePi
=====

#Python Libraries
`flask` - for web api
`pytz` - for timezones

#Wiring Used: [Using BCM Numbers](http://www.raspberrypi-spy.co.uk/wp-content/uploads/2012/06/Raspberry-Pi-GPIO-Layout-Model-B-Plus-rotated-2700x900-1024x341.png)
##Outputs
17 - Garage Door Relay

##Inputs
24 - Man Door Sensor (Wired through Normally Open Contact)
25 - Garage Door Sensor (Wired through Normally Open Contact)

5V Power & Ground supplied where necessary

#Overview
Two applications make up this utility with a backing sqlite database.

##door_reader.py
This application works in a polling loop that waits for a change in door status for either the man door, or the car door. When one opens it saves the timestamp of the event to a variable. When the door closes it calculates the time open (in seconds). Either event logs a line to the database. When the man door is opened the camera takes a picture every iteration of the loop, saving it to a dated folder in the ./pics subdirectory

##web_listener.py
In v1.0 this application has two commands: `signal` and `status` which both listen on the all IPs, port 5000 (default).

* signal - used to signal the door relay to actuate for 500ms
* status - queries the sqlite database for the most recent event for either door