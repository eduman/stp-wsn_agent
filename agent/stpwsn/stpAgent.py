#!/usr/bin/python

#DEPENDENCIES: pyserial
import serial
import sys
import time
import signal
#import select
#import threading
import thread

#COM_PORT = '/dev/ttyACM0' 
COM_PORT = 'COM5'
GATEWAY_NAME = 'gateway_id'
ERROR_MSG = "ST-P Device Angent error, %s: %s\n"

#"bn":"https://dimmer.fit.fraunhofer.de/stp-wsn/rc/<gw-name>/<node-id>/"
myJsonNode= '{"bn":"https://dimmer.fit.fraunhofer.de/stp-wsn/rc/%s/%s/","bt":%s,"e":[%s]}\n'
myJsonSample = '{"n":"%s","u":"%s","v":%s}'
loop = True
input = sys.stdin
out = sys.stdout
err = sys.stderr


def signal_handler(signal, frame):
	close()


def close():
	global loop 
	loop = False

def main():
	# The main thread reads data from the serial port.
	try:
		thread.start_new_thread(readInput, ())
		#ser = serial.Serial(COM_PORT,9600,timeout=1)
		ser = serial.Serial(COM_PORT,9600)
		if not ser.isOpen():
			ser.open()
		signal.signal(signal.SIGINT, signal_handler)
		while(loop):
			try:
				line = ser.readline()
				line = line.strip().replace('\r', '').replace('\n', '')
				if line:
					fields = line.split(';')
					isToBeSent = False
					sample = ""
					nodeID = "Unknown"
					for field in fields:
						if field:
							keyVal = field.split("=")
							if len(keyVal) == 2 and keyVal[0].lower() == "id":
								nodeID = keyVal[1]
								isToBeSent = True	
							elif len (keyVal) == 2 and keyVal[0].lower() == "t":
								val = keyVal[1]
								sample = makeSample(sample, "Temperature", "Cel", val)
							elif len(keyVal) == 2 and keyVal[0].lower() == "h":
								val = keyVal[1]
								sample = makeSample(sample, "Humidity", "Percent", val)
					
					if isToBeSent:
						unixTimeStamp = int(time.time())
						out.write(myJsonNode % (GATEWAY_NAME, nodeID, str(unixTimeStamp), sample))
						#sys.stdout.write(str(fields) + '\n')
						out.flush()

				time.sleep(0.1)
			except serial.serialutil.SerialException, e:
				err.write(ERROR_MSG % ("SerialException", str(e)))
				err.flush()
			except IOError, e:
				err.write(ERROR_MSG % ("IOError", str(e)))
				err.flush()
			except Exception, e:
				err.write(ERROR_MSG % ("Exception", str(e)))
				err.flush()

		if ser.isOpen():
			ser.close()
		sys.exit(0)
	except Exception, e:
		err.write(ERROR_MSG %("Exception", str(e)))
		err.flush()	

def makeSample (outString, name ,unit, value):
	try:
		value = float(value)
		if outString:
			outString += ","
		outString += myJsonSample % (name, unit, str(value))
	except ValueError, e:
		err.write(ERROR_MSG % ("ValueError", str(e)))
		err.flush()
	
	return outString
def readInput():
	# It is the core for a second thread. It reads data from the stdin and 
	# forward them to the stp coordinator via the serial port.
	# TODO: to be implemented
	try:
		while loop:
			line = input.readline()
			line = line.strip().replace('\r', '').replace('\n', '')
			if line:
				if line.lower() == "stp-stop":
					close()
				else:
					err.write(ERROR_MSG % ("Incoming input", "TODO " + line))
					err.flush()
	except Exception, e:
		err.write(ERROR_MSG % ("Exception", str(e)))
		err.flush()
	
	#	try:
	#		while loop and sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
	#			self.line = sys.stdin.readline()
	#			if self.line:
	#				err.write(ERROR_MSG % ("incoming input",line))
	#				err.flush()
	#	except Exception, e:
	#		err.write(ERROR_HEADER % ("Exception", str(e)))
	#		err.flush()
if __name__ == '__main__':
	main()
