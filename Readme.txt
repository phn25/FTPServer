Phuong Nguyen
CS472 - HW4
README
11/19/2018

I tested my server on tux against the ftp client on tux. To run the program on tux, enter the 
following command to command line:
	python3 FtpServer.py <logfilename> <portnum>
where:
	<logfilename>: desired name for the log file
	<portnum>: port number that client should connect to

On another tux terminal, run the ftp client on tux using this command:
	ftp “0.0.0.0” <portnum>
where:
	<portnum>: the same port number that server program uses

After the program run, the server configurations will be printed out. If both passive and
and active mode are restricted, the server will print out an error message and log it in
the server log file. After the server runs, an ip address will then be printed out. This 
ip address is displayed so that it'll be easier for the customed client to know where to
connect to. After that the server runs although nothing will show up on the screen. All 
messages or error message will be recorded in the server log file. Sample log files can be 
found in folder "Sample log files". Since I tested against the ftp client on tux, I didn't 
have the client log file associated with the log files in folder "Sample log files". I 
included the client log files from my HW2 but please note that this log file resulted from
testing my ftp client against ftp tux server, not my ftp server.

Also I didn't implement EPSV and EPRT in hw3 and I didn't have enough time to finish those 
so my server doesn't fully support these commands. But I did add code to check for EPSV 
and EPRT restricted mode so that "check mode" part should work as expected for all commands.

List of commands that can be used (this is the command name from ftp client on tux): 
- USER (used for log in)
- PASS (used for log in)
- cd (please use the full absolutte path when testing)
- cdup
- pwd 
- quit 
- system (SYST)
- dir (LIST)
- help
- passive (PASV)
- get (RETR) (please use the full absolutte path when testing)
- put (STOR) (please use the full absolutte path when testing)
- PORT: I couldn't find the exact command associated to this one on the tux ftp client 
but you can just turn off passive mode (if you're already in passive, simply enter 
"passive", else you're in active mode by default). Then all commands like ls, dir, get, 
and put will run in active mode (PORT).