# Phuong Nguyen
# CS472 - HW3
# Program: FtpServer.py
# 11/12/2018

import socket 
import sys
import time
import os
import random
from _thread import *
import threading
from Log import Log

validCommandList = ["ABOR", "ACCT", "ALLO", "APPE", "CDUP", "CWD", "DELE", "EPRT", "EPSV", "FEAT", "HELP", "LIST", "MDTM", 
					"MKD", "MODE", "NLST", "NOOP", "OPTS", "PASS", "PASV", "PORT", "PWD", "QUIT", "REIN", "REST", "RETR", "RMD", "RNFR", 
					"RNTO", "SITE", "SIZE", "SMNT", "STAT", "STOR", "STOU", "STRU", "SYST", "TYPE", "USER", "XCUP", "XCWD", "XMKD", 
					"XPWD", "XRMD"]
usedPortNum = []

"""
recv_timeout(clientSocket, l, timeout = 1)
	Make sure that all data sent from client is read and that server is not missing anything
	@param socket
		Initialized and connected socket
	@param l
		Server's output log file 
	@param timeout
		Timeout time 
"""
def recv_timeout(clientSocket, l, timeout = 1):
	clientSocket.setblocking(0)

	totalDataReceived = []
	currentBytesRead = ''

	start = time.time()

	# keep looking for data till decent timeout
	while True:
		# if server receives something
		if totalDataReceived and time.time() - start > timeout:
			break

		# if server receives nothing after a while => timeout
		elif time.time() - start > 180 * timeout:
			doTimeOut(clientSocket, l)
		
		try:
			currentBytesRead = clientSocket.recv(4096)
			if currentBytesRead:
				totalDataReceived.append(str(currentBytesRead, 'ascii').strip("\r\n")) 
				start = time.time()
			else: # if currentBytesRead is None, wait a little and try reading again
				time.sleep(0.1)
		except:
			pass

	return ''.join(totalDataReceived)

"""
getTransferData_timeout(clientSocket, l, timeout = 1)
	Is used specifically when reading data in file transfer command
	Make sure that all data sent from client is read and that server is not missing anything
	@param socket
		Initialized and connected socket
	@param l
		Server's output log file 
	@param timeout
		Timeout time 
"""
def getTransferData_timeout(clientSocket, l, timeout = 1):
	clientSocket.setblocking(0)

	totalDataReceived = []
	currentBytesRead = ''

	start = time.time()

	# keep looking for data till decent timeout
	while True:
		# if server receives something
		if totalDataReceived and time.time() - start > timeout:
			break

		# if server receives nothing after a while => timeout
		elif time.time() - start > 180 * timeout:
			doTimeOut(clientSocket, l)
		
		try:
			currentBytesRead = clientSocket.recv(4096)
			if currentBytesRead:
				totalDataReceived.append(str(currentBytesRead, 'ascii').strip("\r\n"))  
				start = time.time()
			else: # if currentBytesRead is None, wait a little and try reading again
				time.sleep(0.1)
		except:
			pass

	# for reading data inside a file, data received must be joined using "\n"
	return '\n'.join(totalDataReceived)


"""
doTimeout(socket, l)
	Close all socket connection and log file when there's a timeout
	Notify client of the timeout
	@param socket
		Initialized and connected socket
	@param l
		Server's output log file 
"""
def doTimeOut(socket, l):
	print("Timeout")
	try:
		socket.send(bytes('421 Timeout.\r\n', 'ascii')) 
	except:
		pass
	l.log("Sent", "421 Timeout.")
	l.close()
	socket.close()
	os._exit(1) # exit the entire system when there's timeout
	

"""
isValidUser(user, password)
	Authenticate users, checking if their credentials is in a user configs file, and return True if it is. Return False otherwise.
	Raise exception if the user config file does not exit
	@param user
		User name of an user
	@param password
		The password associated to that user
"""
def isValidUser(user, password):
	usr = user + "-" + password # concatenate to match the format in the user config file
	try:
		f = open("FtpUsers.txt", "r")
		credentials = f.readlines()
		validUser = False
	except FileNotFoundError:
		print("Could not find user config file.")
		return False

	for credential in credentials:
		if usr == credential:
			validUser = True

	f.close()
	return validUser


"""
doCWD(socket, l, path)
	Implement the CWD command
	Change the working directory on the server
	Send the client reply with code number and description
	@param socket
		Initialized and connected socket
	@param l
		Server's output log file 
	@param path
		Directory path to change to 
"""
def doCWD(socket, l, path):
	try:
		os.chdir(path)
		socket.send(bytes('250 Directory successfully changed.\r\n', 'ascii'))
		l.log("Sent", "250 Directory successfully changed.")
	except OSError as err:
		socket.send(bytes('550 Failed to change directory.\r\n', 'ascii'))
		l.log("Sent", "550 Failed to change directory.")
	return

"""
doCDUP(socket, l)
	Implement the CDUP command
	Change the current working directory to its parent directory
	Send the client reply with code number and description
	@param socket
		Initialized and connected socket
	@param l
		Server's output log file 
"""
def doCDUP(socket, l):
	path = "../"
	try:
		os.chdir(path)
		# NOTE: check if there're any other response messages for cdup, check if this uses 200 or 250 code
		socket.send(bytes('250 Directory successfully changed.\r\n', 'ascii'))
		l.log("Sent", "250 Directory successfully changed.")
	except OSError as err:
		socket.send(bytes('550 Failed to change directory.\r\n', 'ascii'))
		l.log("Sent", "550 Failed to change directory.")
	return


"""
doPASV(socket_, l, serverAddr, port)
	Implement the PASV command
	Create a socket connection to the server ip address using a random port for data transfer 
	Tells client to do data transfer using that socket
	Send the client reply with code number and description
	Must be followed by a LIST or STOR OR RETR command
	@param socket_
		The initial connected socket
	@param l
		Server's output log file 
	@param serverAddr
		The server ip address  
"""
def doPASV(socket_, l, serverAddr, clientAddr, port):
	dataPort = random.randint(1025, 65535) 
	while dataPort == port or dataPort in usedPortNum: # make sure port is not in use
		dataPort = random.randint(1025, 65535)
	usedPortNum.append(dataPort)

	p1 = dataPort // 256
	p2 = dataPort % 256

	try:
		dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create an INET, STREAMing clientSocket
		dataSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		dataSocket.bind((serverAddr, dataPort)) 
		dataSocket.listen() # become a server socket

		server = serverAddr.replace(".", ",") 
		message = "227 Entering Passive Mode ({serverAddr},{p1},{p2}).\r\n".format(serverAddr=server, p1=p1, p2=p2)
		socket_.send(bytes(message, 'ascii')) # send back the new data socket info so client can connect to it
		l.log("Sent", message.strip("\r\n"))

		(clientDataSocket, address) = dataSocket.accept()

		address = ' '.join(str(v) for v in address).split(" ") # convert to ip address of form xxx.xxx.xxx.xxx
		clientAddr = clientAddr.split(" ")

		# check if server is talking to the right client
		if clientAddr[0] != address[0]:
			print(clientAddr[0])
			print(address[0])
			socket_.send(bytes('425 Server drops the connection. Please try again.\r\n', 'ascii'))
			l.log_("An unrecognized device with address {address} attempts to connect. Drop data connection".format(address=address[0]))
			dataSocket.close() # drop the connection if the client's ip address doesn't match
			return

	except Exception as e:
		l.log_(str(e))
		try:
			socket_.send(bytes('425 No connection was established.\r\n', 'ascii'))
			l.log("Sent", "425 No connection was established.")
		except Exception as err:
			l.log_(str(err))
		return

	message = "Open a connection on port {port} in PASV mode for data transfer".format(port=dataPort)
	l.log_(message)

	# get the next command that client types in, this command must be either LIST, STOR, or RETR
	receivedCommand = recv_timeout(socket_, l) 
	l.log("Received", receivedCommand)
	receivedCommand = receivedCommand.split(" ", 1)

	if receivedCommand[0] == "LIST":
		if len(receivedCommand) <= 2:
			path = ""
			if len(receivedCommand) == 1: # if no path specified, use the current directory
				path = "."
			elif len(receivedCommand) == 2:
				path = receivedCommand[1]
			doList(socket_, clientDataSocket, l, path)
		else:
			socket_.send(bytes('501 Syntax error in parameters or argument.\r\n', 'ascii'))
			l.log("Sent", "501 Syntax error in parameters or argument.")
	elif receivedCommand[0] == "STOR":
		if len(receivedCommand) == 2: # STOR must have 2 arguments
			path = receivedCommand[1]
			doSTOR(socket_, clientDataSocket, l, path)
		else:
			socket_.send(bytes('501 Syntax error in parameters or argument.\r\n', 'ascii'))
			l.log("Sent", "501 Syntax error in parameters or argument.")
	elif receivedCommand[0] == "RETR":
		if len(receivedCommand) == 2: # RETR must have 2 arguments
			path = receivedCommand[1]
			doRETR(socket_, clientDataSocket, l, path)
		else:
			socket_.send(bytes('501 Syntax error in parameters or argument.\r\n', 'ascii'))
			l.log("Sent", "501 Syntax error in parameters or argument.\r\n")
	else:
		try:
			socket.send(bytes('500 Unknown command.\r\n', 'ascii'))
			l.log("Sent", "500 Unknown command.")
		except:
			pass
	dataSocket.close() # after data transfer completes, close the data socket


"""
doEPSV(socket, l)
	Implement the EPSV command
	@param socket
		The initial connected socket
	@param l
		Server's output log file 
"""
def doEPSV(socket, l):
	socket.send(bytes('502 Command not implemented.\r\n', 'ascii'))
	l.log("Sent", "502 Command not implemented.")


"""
doEPRT(socket, l)
	Implement the EPSV command
	@param socket
		The initial connected socket
	@param l
		Server's output log file 
"""
def doEPRT(socket, l):
	socket.send(bytes('502 Command not implemented.\r\n', 'ascii'))
	l.log("Sent", "502 Command not implemented.")


"""
doPORT(socket_, l, serverAddr, receivedMessage)
	Implement the PORT command
	Use an ipaddress and port number that client sends through the PORT command to connect to an already created socket in client for data transfer 
	Send the client reply with code number and description
	Must be followed by a LIST or STOR OR RETR command
	@param socket_
		The initial connected socket
	@param l
		Server's output log file 
	@param serverAddr
		The server ip address  
	@param receivedMessage
		The arguments from the PORT command that client sends  
"""
def doPORT(socket_, l, serverAddr, receivedMessage):
	message = receivedMessage[1]
	message = message.split(",")
	
	if len(message) == 6:
		clientAddr = ".".join(message[:4]) # get the ip address from the received message
		dataPort = int(message[4]) * 256 + int(message[5]) # get the port number from the received message

		socket_.send(bytes('200 Command OK.\r\n', 'ascii'))
		l.log("Sent", "200 Command OK.\r\n")

		try:
			dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create an INET, STREAMing clientSocket
			dataSocket.connect((clientAddr, dataPort)) # connect to a data socket server that's already created in client
			l.logConnectionInfo(clientAddr, str(dataPort)) 

			# get the next command that client types in, this command must be either LIST, STOR, or RETR
			receivedCommand = recv_timeout(socket_, l) # 
			l.log("Received", receivedCommand)
			receivedCommand = receivedCommand.split(" ", 1)

			if receivedCommand[0] == "LIST":
				if len(receivedCommand) <= 2: 
					path = ""
					if len(receivedCommand) == 1:
						path = "."
					elif len(receivedCommand) == 2:
						path = receivedCommand[1]
					doList(socket_, dataSocket, l, path)
				else:
					socket_.send(bytes('501 Syntax error in parameters or argument.\r\n', 'ascii'))
					l.log("Sent", "501 Syntax error in parameters or argument.\r\n")
			elif receivedCommand[0] == "STOR":
				if len(receivedCommand) == 2: # STOR must have 2 arguments
					path = receivedCommand[1]
					doSTOR(socket_, dataSocket, l, path)
				else:
					socket_.send(bytes('501 Syntax error in parameters or argument.\r\n', 'ascii'))
					l.log("Sent", "501 Syntax error in parameters or argument.\r\n")
			elif receivedCommand[0] == "RETR":
				if len(receivedCommand) == 2: # RETR must have 2 arguments
					path = receivedCommand[1]
					doRETR(socket_, dataSocket, l, path)
				else:
					socket_.send(bytes('501 Syntax error in parameters or argument.\r\n', 'ascii'))
					l.log("Sent", "501 Syntax error in parameters or argument.\r\n")
			else:
				try:
					socket.send(bytes('500 Unknown command.\r\n', 'ascii'))
					l.log("Sent", "500 Unknown command.")
				except:
					pass
		except Exception as e: # if can't connect to the data server socket in client
			l.log_(str(e))
			try:
				socket_.send(bytes('425 No connection was established.\r\n', 'ascii'))
				l.log("Sent", "425 No connection was established.\r\n")	
			except Exception as err:
				l.log_(str(err))
	else: # if the syntax for PORT command is wrong
		socket_.send(bytes('501 Server cannot accept argument.\r\n', 'ascii'))
		l.log("Sent", "501 Server cannot accept argument.")
	dataSocket.close()

"""
doList(serverSocket, dataSocket, l, path)
	Implement the LIST command
	If path is a directory, send back the list of all entries inside that directory
	If path is a file, send back the content of that file
	Send client the data with code number and description
	Must follow a PASV or PORT command
	@param serverSocket
		The initial connected socket
	@param dataSocket
		The socket that either PASV or PORT creates specifically for data transfer 
	@param l
		Server's output log file  
	@param path
		Pathname to get listing data from  
"""
def doList(serverSocket, dataSocket, l, path):
	serverSocket.send(bytes('150 Here comes the directory listing.\r\n', 'ascii')) 
	l.log("Sent", "150 Here comes the directory listing.")

	try:
		if os.path.isdir(path): # if the path is directory
			message = os.listdir(path) # list all entries inside 
			message = "\n".join(message) + "\r\n"
			dataSocket.send(bytes(message, 'ascii')) # send + log the data back
			l.log("Sent", message)
		else: # if the path is file
			try:
				f = open(path, "r") # open and read its content
				message = f.readlines()
				message = ''.join(message) + "\r\n"
				dataSocket.send(bytes(message, 'ascii'))
				l.log("Sent", message)
			except FileNotFoundError:
				serverSocket.send(bytes('451 Server could not find the specified file for directory listing.\r\n', 'ascii'))
				l.log("Sent", "451 Server could not find the specified file for directory listing.")
				return
	except OSError:
		serverSocket.send(bytes('451 Server had trouble reading the directory from disk.\r\n', 'ascii'))
		l.log("Sent", "451 Server had trouble reading the directory from disk.")
		return
	
	# send successful message
	serverSocket.send(bytes('226 Directory send OK.\r\n', 'ascii'))
	l.log("Sent", "226 Directory send OK.")


"""
doSTOR(serverSocket, dataSocket, l, path)
	Implement the STOR command
	Put a client specified file to the server
	Send client back the code number and description
	Must follow a PASV or PORT command
	@param serverSocket
		The initial connected socket
	@param dataSocket
		The socket that either PASV or PORT creates specifically for data transfer 
	@param l
		Server's output log file  
	@param path
		Pathname of the location/file to put the data
"""
def doSTOR(serverSocket, dataSocket, l, path):
	try:
		f = open(path, "w") # open a file to read data from
		serverSocket.send(bytes('150 Accept the specified path.\r\n', 'ascii'))
		l.log("Sent", "150 Accept the specified path.")
		fileDataReceived = getTransferData_timeout(dataSocket, l) # get content of that file

		message = f.writelines(fileDataReceived) # put the content into the specified path/filename
		serverSocket.send(bytes('226 File transfer completed.\r\n', 'ascii'))
		l.log("Sent", "226 File transfer completed.")
		f.close()
	except Exception as err:
		serverSocket.send(bytes('451 Server had trouble saving file to disk because ' + str(err) + '\r\n', 'ascii'))
		l.log("Sent", "451 Server had trouble saving file to disk because " + str(err) + "\r\n")


"""
doRETR(serverSocket, dataSocket, l, path):
	Implement the RETR command
	Get content of a file from server
	Send client back the code number and description
	Must follow a PASV or PORT command
	@param serverSocket
		The initial connected socket
	@param dataSocket
		The socket that either PASV or PORT creates specifically for data transfer 
	@param l
		Server's output log file  
	@param path
		Pathname of the location/file to get the data
"""
def doRETR(serverSocket, dataSocket, l, path):
	serverSocket.send(bytes('150 Here comes the file listing.\r\n', 'ascii'))
	l.log("Sent", "150 Here comes the file listing.")

	try:
		f = open(path, "r") # open the file
		message = f.readlines() # read content of that file
		message = ''.join(message) + "\r\n"
		dataSocket.send(bytes(message, 'ascii')) # send back the data
		l.log("Sent", message)

		serverSocket.send(bytes('226 File transfer completed.\r\n', 'ascii'))
		l.log("Sent", "226 File transfer completed.")
	except Exception as e: # handle errors
		serverSocket.send(bytes('451 Server had trouble retrieving the specified file.\r\n', 'ascii'))
		l.log("Sent", "451 Server had trouble retrieving the specified file.")


"""
doPWD(socket, l):
	Implement the PWD command
	Print out the current working directory
	Send client back the code number and description
	@param socket
		The initial connected socket
	@param l
		Server's output log file  
"""
def doPWD(socket, l):
	try:
		message = "257 {pwd} is the current directory.\r\n".format(pwd=os.getcwd())
		socket.send(bytes(message, 'ascii'))
		l.log("Sent", message.strip("\r\n"))
	except Exception as err:
		socket.send(bytes('500 Server had trouble printing out the current directory.\r\n', 'ascii'))
		l.log("Sent", "500 Server had trouble printing out the current directory.")


"""
doSYST(socket, l):
	Implement the PWD command
	Print out the server system information
	Send client back the code number and description
	@param socket
		The initial connected socket
	@param l
		Server's output log file  
"""
def doSYST(socket, l):
	try:
		message = "215 {sysType}\r\n".format(sysType=sys.platform)
		socket.send(bytes(message, 'ascii'))
		l.log("Sent", message.strip("\r\n"))
	except Exception as err:
		socket.send(bytes('500 Server had trouble printing out the system information.\r\n', 'ascii'))
		l.log("Sent", "500 Server had trouble printing out the system information.")


"""
doHelp(socket, l, cmdName):
	Implement the HELP command
	Print out useful information about available commands on the server
	Send client back the code number and description
	@param socket
		The initial connected socket
	@param l
		Server's output log file  
"""
def doHelp(socket, l, cmdName):
	helpMsg = ""
	if cmdName != "" and cmdName not in validCommandList:
		helpMsg = "502 Unknown command {cmd}.\r\n".format(cmd=cmdName)
	else:
		helpMsg = "214-The following commands are recognized.\n" 
		helpMsg += " ".join(validCommandList[:13]) + "\n" 
		helpMsg += " ".join(validCommandList[13:28]) + "\n"
		helpMsg += " ".join(validCommandList[28:42]) + "\n"
		helpMsg += " ".join(validCommandList[42:]) + "\n"
		helpMsg += "214 Help OK.\r\n"
	# NOTE check if there're any other messages for help
	socket.send(bytes(helpMsg, 'ascii'))
	l.log("Sent", helpMsg)


"""
doQUIT(socket, l):
	Implement the QUIT command
	Tell the server to close the session
	Send client back the code number and description
	@param socket
		The initial connected socket
	@param l
		Server's output log file  
"""
def doQuit(socket, l):
	try:
		socket.send(bytes('221 Goodbye.\r\n', 'ascii'))
		l.log("Sent", "221 Goodbye.") 
	except Exception as err:
		l.log_(str(err))
	l.close()
	os._exit(0)


"""
doOtherCommands(socket, serverAddr, port, l):
	Receive request after client's signed in and execute it by calling the appropriate command function 
	Must be called after the doUSERandPASS function
	Send client back the code number and description
	@param socket
		The initial connected socket
	@param serverAddr
		Server's ip address  
	@param port
		The port number of the socket connection
	@param l
		Server's output log file
	@param configs
		Server's configuration file
"""
def doOtherCommands(socket, serverAddr, clientAddr, port, l, configs):
	receivedMessage = recv_timeout(socket, l)
	l.log("Received", receivedMessage)
	receivedMessage = receivedMessage.split(" ", 1)

	while receivedMessage[0] != "QUIT": # process the
		if receivedMessage[0] == "CWD":
			if len(receivedMessage) < 2:
				socket.send(bytes('550 Failed to change directory.\r\n', 'ascii'))
				l.log("Sent", "550 Failed to change directory.")
			else:
				doCWD(socket, l, receivedMessage[1])
		elif receivedMessage[0] == "CDUP":
			doCDUP(socket, l)
		elif receivedMessage[0] == "PASV": 
			if configs["pasv_mode"] == "NO":
				socket.send(bytes('500 Passive mode is restricted. Use active mode instead.\r\n', 'ascii'))
				l.log("Sent", "500 Passive mode is restricted. Use active mode instead.")
			else:
				doPASV(socket, l, serverAddr, clientAddr, port)
		elif receivedMessage[0] == "EPSV":
			if configs["epsv_mode"] == "NO":
				socket.send(bytes('500 Passive mode is restricted. Use active mode instead.\r\n', 'ascii'))
				l.log("Sent", "500 Passive mode is restricted. Use active mode instead.")
			else:
				doEPSV(socket, l)
		elif receivedMessage[0] == "PORT": 
			if configs["port_mode"] == "NO":
				socket.send(bytes('500 Active mode is restricted. Use passive mode instead.\r\n', 'ascii'))
				l.log("Sent", "500 Active mode is restricted. Use passive mode instead.")
			else:
				doPORT(socket, l, serverAddr, receivedMessage)
		elif receivedMessage[0] == "EPRT":
			if configs["eprt_mode"] == "NO":
				socket.send(bytes('500 Active mode is restricted. Use passive mode instead.\r\n', 'ascii'))
				l.log("Sent", "500 Active mode is restricted. Use passive mode instead.")
			else:
				doEPRT(socket, l)
		elif receivedMessage[0] == "RETR": # must be called after PASV or PORT
			socket.send(bytes('425 Use PORT or PASV first.\r\n', 'ascii'))
			l.log("Sent", "425 Use PORT or PASV first.")
		elif receivedMessage[0] == "STOR": # must be called after PASV or PORT
			socket.send(bytes('425 Use PORT or PASV first.\r\n', 'ascii'))
			l.log("Sent", "425 Use PORT or PASV first.")
		elif receivedMessage[0] == "PWD":
			doPWD(socket, l)
		elif receivedMessage[0] == "SYST":
			doSYST(socket, l)
		elif receivedMessage[0] == "LIST": # must be called after PASV or PORT
			socket.send(bytes('425 Use PORT or PASV first.\r\n', 'ascii'))
			l.log("Sent", "425 Use PORT or PASV first.")
		elif receivedMessage[0] == "HELP":
			cmdName = ''
			if len(receivedMessage) > 1:
				cmdName = receivedMessage[1]
			doHelp(socket, l, cmdName)
		elif receivedMessage[0] == "":
			pass
		else:
			try:
				socket.send(bytes('500 Unknown command.\r\n', 'ascii'))
				l.log("Sent", "500 Unknown command.")
			except:
				break
		receivedMessage = recv_timeout(socket, l)
		l.log("Received", receivedMessage)
		receivedMessage = receivedMessage.split(" ")

	doQuit(socket, l)

	return


"""
doUSERandPASS(socket, serverAddr, port, l):
	Implement the USER and PASS command
	Receive the client's credentials and authenticate the client 
	Call doOtherCommands function after the credential is validated
	Send client back the code number and description
	@param socket
		The initial connected socket
	@param serverAddr
		Server's ip address  
	@param port
		The port number of the socket connection
	@param l
		Server's output log file
	@param configs
		Server's configuration file
"""
def doUSERandPASS(socket, serverAddr, clientAddr, port, l, configs):
	receivedMessage = recv_timeout(socket, l) # get the client's username
	l.log("Received", receivedMessage)
	receivedMessage = receivedMessage.split(" ", 1)

	# check for valid USER command
	if receivedMessage[0] != "USER" or len(receivedMessage) < 2:
		socket.send(bytes('503 Login with USER first.\r\n', 'ascii'))
		l.log("Sent", "503 Login with USER first.")
	else:
		user = receivedMessage[1]
		socket.send(bytes('331 Please specify the password.\r\n', 'ascii'))
		l.log("Sent", "331 Please specify the password.")

		receivedMessage = recv_timeout(socket, l) # get the client's password
		l.log("Received", receivedMessage)
		receivedMessage = receivedMessage.split(" ")

		# check for valid PASS command
		if receivedMessage[0] != "PASS" or len(receivedMessage) < 2:
			socket.send(bytes('500 Unknown command. Login with PASS first.\r\n', 'ascii')) 
			l.log("Sent", "500 Unknown command. Login with PASS first.")
		else:
			password = receivedMessage[1]
			if not isValidUser(user, password): # authenticate
				socket.send(bytes('530 Login incorrect.\r\n', 'ascii')) 
				l.log("Sent", "530 Login incorrect.")
			else:
				socket.send(bytes('230 Login successful.\r\n', 'ascii'))
				l.log("Sent", "230 Login successful.")

				doOtherCommands(socket, serverAddr, clientAddr, port, l, configs) 


"""
runServer(socket, serverAddr, port, l):
	Run the server concurrently
	Call doUSERandPASS function after connection is succesfully made
	Send client back the code number and description
	@param socket
		The initial connected socket
	@param serverAddr
		Server's ip address  
	@param port
		The port number of the socket connection
	@param l
		Server's output log file
	@param configs
		Server's configuration file
"""
def runServer(socket, serverAddr, clientAddr, port, l, configs):
	# send message back to client to signify a successful connection 
	socket.send(bytes('220 Welcome to cs472 hw3 FTP server\r\n', 'ascii')) 
	l.log("Sent", "220 Welcome to cs472 hw3 FTP server")

	doUSERandPASS(socket, serverAddr, clientAddr, port, l, configs)


def main() :
	serverAddr = ""
	random.seed()
	# get the command line arguments
	if len(sys.argv) < 3:
		print ("Invalid numbers of arguments provided. Please try again")
		sys.exit(1)

	logFileName = sys.argv[1]
	port = sys.argv[2]

	if not port.isdigit() and int(port) < 1024: # check for valid port number
		print("Please use a port number greater than 1024")
		sys.exit(1)
			
	port = int(port)
	usedPortNum.append(port) # append to keep track of which port is in used

	l = Log() # open the log file
	l.setAndOpenFile(logFileName)

	# open configuration file
	try:
		f = open("ftpserverd.conf", "r")
		allLines = f.readlines()
	except FileNotFoundError:
		print("Cannot find server configuration file.")
		l.log_("Cannot find server configuration file.")
		l.close()
		sys.exit(1)

	configs = {}

	for line in allLines:
		if not line.startswith("#"):
			mode = line.split("=")[0].lower().strip(" ")
			status = line.split("=")[1].upper().strip(" \n")
			configs[mode] = status

	print(configs)
	l.log_(str(configs))

	if configs["port_mode"] == "NO" and configs["pasv_mode"] == "NO":
		print("Fatal error. Both port_mode and part_mode are restricted.")
		l.log_("Fatal error. Both port_mode and part_mode are restricted.")
		l.close()
		sys.exit(1)

	# create socket
	try:
		serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create an INET, STREAMing clientSocket
		serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# serverAddr = socket.gethostbyname(socket.gethostname())
		serverAddr = "0.0.0.0"
		print(serverAddr)
		serverSocket.bind((serverAddr, port)) 	# bind the clientSocket to a public host, and an arbitrary port
		serverSocket.listen(5) # become a server 

	except socket.error as err:
		errMsg = "Socket creation and connection failed with error %s" %(err)
		l.log_(errMsg)
		l.close()
		sys.exit(1)

	# start the server
	while True:
		try:
			clientSocket, address = serverSocket.accept()
			clientAddr = ' '.join(str(v) for v in address)
			l.logConnectionInfo(clientAddr, str(port))
			start_new_thread(runServer, (clientSocket, serverAddr, clientAddr, port, l, configs))
		except Exception as error:
			l.log_(str(error))
			sys.exit(1)

	l.close()
	serverSocket.close()
	
if __name__ == "__main__" :
	main()
