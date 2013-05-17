#!/usr/bin/python
#This script is only supported on build server that support mcpenv command.
import os
import sys
import commands
import socket
import telnetlib
import time
import subprocess

def parse_request_code(s):  #this function is used to get request code in CLI
	s=s.replace('\r','')
	s=s.replace('\n','')
	return s[s.index('dbgshimm')+8:s.index('Please')]

def inkey():  #this function is used to get a key pressed by user
	import sys, tty, termios
	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)
	try:
	    tty.setraw(sys.stdin.fileno())
	    ch = sys.stdin.read(1)
	finally:
	    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
	return ch
def avert_telnet_hung():   #this function is used to avoid blocking in CLI
	try:
		tn.write(error_response_code)
		time.sleep(1)
		# 'Please press Control+D to exit'
		tn.write('\04')
		time.sleep(1)
		tn.write('exit\n')
		time.sleep(1)
		tn.close()
	except Exception,e:
		print 'error happened in CLI,the CLI may not be available until you reset the IMM.'
		sys.exit(1)
	
if(len(sys.argv)==1):
	print 'please specify IMM IP using \"dbgshimm ip\"'
	sys.exit(1)
try:
	hostip=sys.argv[1]		# used to store the specified ip.
except:
	print 'please specify IMM ip using \"dbgshimm ip\"'
	sys.exit(1)
try:
	socket.inet_aton(hostip)
except:
	print 'It is an illegal ip. Please specify IMM IP using \"dbgshimm ip\"'
	sys.exit(1)
user='USERID'
passwd='PASSW0RD'
telnet_cmd='dbgshimm'
error_response_code='DEADC0DE0000000300000100C1A097105D917517F1B2D482E7B428BB03AB433DFD28E6E25'
supported_options=['-U','-P']	# the supported option list.
if(len(sys.argv)>2):			# when there is attached options by users.
	# if there's incorrect options, prompt user to read the documentation
	if(sys.argv[2] not in supported_options or sys.argv[4] not in supported_options):
		print 'Usage:dbgshimm ip or dbgshimm ip -U XXXX -P ****'
		sys.exit(1)
	i=0;
	while i<len(supported_options):	### parse the options user attached and initialize the relevant arguments
		if supported_options[i] in sys.argv:
			#print supported_options[i];
			index=sys.argv.index(supported_options[i])
			option=i;
			#print i
			if option==0:
				try:
					user=sys.argv[index+1]
				except:
					print 'please specify the username after -U'
					sys.exit(1)
			if option==1:
				try:
					passwd=sys.argv[index+1]
				except:
					print 'please specity the password after -P'
					sys.exit(1)
		i=i+1;

print 'Trying to telnet '+hostip+' .......'
tn=telnetlib.Telnet();
try:
	tn.open(hostip)
except:
	print 'Cannot connect to host,check your connection to '+hostip
	sys.exit(1)
#print user," ",passwd
try:
	tn.read_until('login: ',8)
	tn.write(user+'\n')
	tn.read_until('Password: ',8)
	tn.write(passwd+'\n')
except:
	print 'Connection closed by foreign host.\nUnable to telnet to IMM\'s default port.'
	sys.exit(1)
time.sleep(3)
try:
	if(tn.expect(['MYIMM>','system>'],8)[1]==None):
		print 'Login failed as unable to telnet to designated ip with default credential USERID/PASSW0RD.'
		sys.exit(1);
except Exception,e:
	print 'Telnet login failed.'
	sys.exit(1)
print 'Logined into CLI successfully.\nNow run dbgshimm command in CLI.'
try:
	tn.write(telnet_cmd+'\n')
	time.sleep(1)
except Exception,e:
	print 'Failed to execute dbgshimm command in CLI!'
	sys.exit(1)
try:
	mesg=tn.read_very_eager()
	time.sleep(5)
except Exception,e:
	print 'Read data from CLI Interrupted!'
	sys.exit(1)
try:
	req_code=parse_request_code(mesg)
except Exception,e:
	print 'Read response code failed in \'dbgshimm\' command!It may be owe to network delay.Please try again!'
	#print str(e)
	avert_telnet_hung()
	sys.exit(1)
print 'Get request code from CLI successfully.'
try:
	f=open('_req_','w')
except:
	#f.close();
	print 'Cannot create temporay file \'_req_\' in current path.You need enough permission in current path to run the script.'
	avert_telnet_hung()
	os.system('rm _req_')
	sys.exit(1)
try:
	f.write('debug_sign\n')
	f.write(req_code)
	f.close();
except Exception,e:
	print 'failed to write request code from CLI to tmp file'
	avert_telnet_hung()
	os.system('rm _req_')
	sys.exit(1)
print 'Now write request code into debug_sign under fakeroot to get response code.'
try:
	f0=open('_req_','r')
	f1=open('_out_','w')
	f2=open('_error_','w')
except:
	print 'Cannot open temporay file \'_req_\' or \'_out_\' or \'_error_\' in current path.'
	avert_telnet_hung()
	os.system('rm _out_ _req_ _error_')
	sys.exit(1)
try:
	test=subprocess.Popen('mcpenv2', shell=False,stdin=f0,stdout=f1,stderr=f2)
except:#if failed to change into root identity,so it should be root identity current,so direct use the root identity,no need to change identity.
#	print 'Failed to change to fakeroot identity using command \'mcpenv2\'! Check if it is supported on your host,please.Or you are under fakeroot identity already,next step will be on.'
	try:
		f=open('_request_','w')
	except:
		#f.close();
		print 'Cannot create temporay file \'_request_\' in current path.'
		avert_telnet_hung()
		os.system('rm _request_')
		sys.exit(1)
	try:
		f.write(req_code)
		f.close();
	except Exception,e:
		print 'Failed to write request code into temporary file.'
		os.system('rm _out_ _req_ _error_ _request_')
		#os.system('rm _request_')
		sys.exit(1)
	try:
		f3=open('_request_','r')
	except Exception,e:
		print 'Failed to open temporary file!'
		os.system('rm _out_ _req_ _error_ _request_')
		#os.system('rm _request_')
		sys.exit(1)
	try:
		test1=subprocess.Popen('debug_sign', shell=False,stdin=f3,stdout=f1,stderr=f2)
	except:
		print 'Failed to run \'debug_sign\' command under fakeroot identity. Please change identity to fakeroot using \'mcpenv\' to check if command \'debug_sign\' is supported!'
		avert_telnet_hung()
		f0.close();
		os.system('rm _out_ _req_ _error_ _request_')
		sys.exit(1)
	try:
		time.sleep(2)
		f0.close()
		f1.close()
		f2.close()
		f3.close()
		f1=open('_out_','r')
		lines=f1.readlines()
		response=lines[7:]
	except:
		print 'File operation error on temporary files.'
		os.system('rm _out_ _req_ _error_ _request_')
		sys.exit(1)
	print 'Get response code from debug_sign successfully.\nNow write response code into CLI to open the debug mode.'
	try:
		for code in response:
			tn.write(code)
		tn.write('\04')
		time.sleep(1)
	except:
		print 'Failed to write response code in CLI.'
		sys.exit(1)
	if(tn.expect(['Executed debug response error'],5)[0]!=-1):
		print 'Failed to write debug response code in CLI.'
		os.system('rm _out_ _req_ _error_ _request_')
		sys.exit(1)
	else:
		print 'Write response code into CLI successfully.\nLow security mode is opened.'
	try:
		tn.write('exit\n')
		time.sleep(1)
		tn.close()
		del tn
	except:
		print 'Failed to exit CLI.'
		os.system('rm _out_ _req_ _error_ _request_')
		sys.exit(1)
	os.system('rm _out_ _req_ _error_ _request_')
	print 'Now connect to host via ssh ..........'
	#os.system('rm _out_ _req_ _error_ _request_')
	os.system('ssh -p 122 immdebug@'+hostip)
	sys.exit(1)
	
try:
	time.sleep(2)
	f0.close()
	f1.close()
	f2.close()
	#f3.close()
	f1=open('_out_','r')
	lines=f1.readlines()
	response=lines[7:]
except:
	print 'File operation error on temporary files.'
	os.system('rm _out_ _req_ _error_')
	sys.exit(1)
print 'Get response code from debug_sign successfully.\nNow write response code into CLI to open the debug mode.'
try:
	for code in response:
		tn.write(code)
	tn.write('\04')
	time.sleep(1)
except:
	print 'Failed to write response code in CLI.'
	os.system('rm _out_ _req_ _error_')
	sys.exit(1)
if(tn.expect(['Executed debug response error'],5)[0]!=-1):
	print 'Failed to write debug response code in CLI.'
	os.system('rm _out_ _req_ _error_')
	sys.exit(1)
else:
	print 'Write response code into CLI successfully.\nLow security mode has been opened.'
try:
	tn.write('exit\n')
	time.sleep(1)
	tn.close()
	del tn
except:
	print 'Failed to exit CLI.'
	os.system('rm _out_ _req_ _error_')
	sys.exit(1)
os.system('rm _out_ _req_ _error_')
print 'Now connect to host via ssh ..........'
#os.system('rm _out_ _req_ _error_ _request_')
os.system('ssh -p 122 immdebug@'+hostip+' checkprocs')
#sys.exit(1)
#process=subprocess.Popen('ssh -p 122 immdebug@'+hostip+' env',shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
#time.sleep(2)
#output,stderr=process.communicate()
#time.sleep(1)
#print output
