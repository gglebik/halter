#!/usr/bin/python -tt
import sys
import urllib
import urllib2
import json
from pprint import pprint
import time
import hmac
import base64
import hashlib

api_url     = 'https://cc.activecloud.com/client/api'
#real user
apikey      = 'apikeiishere'
secret      = 'secretishere'

exception_id = [
                u'00000',
            ]

phone_whitelist = [
            u'79111234567',
            ]
log_file = '/var/log/halter.log'

class CloudServer(object):
	def __init__(self, api_url, apikey, secret):
		self.api_url = api_url
		self.apikey = apikey
		self.secret = secret

	def request(self, args):
		args['apiKey'] = self.apikey
		params = []

		# sort keys
		keys = sorted(args.keys())
		for k in keys:
			params.append(k + '=' + urllib.quote_plus(args[k]))

		# create signature
		query = '&'.join(params)
		digest = hmac.new(self.secret, msg=query.lower(), digestmod=hashlib.sha1).digest()
		signature = base64.b64encode(digest)

		# build url request
		query += '&signature=' + urllib.quote_plus(signature)
		self.value = self.api_url + '?' + query

		# response
		response = urllib2.urlopen(self.value)
		self.decoded = json.loads(response.read())
		return self.decoded

def log(message):
	ctime = time.strftime("%d/%m/%Y-%H:%M:%S")
	f = open(log_file,'a')
	f.write(ctime + ' ' + message + '\n')
	f.close()	

def sms2api(cmd):
	if cmd == 'stop':
		command = 'stopVirtualMachine'
	elif cmd == 'start':
		command = 'startVirtualMachine'
	elif cmd == 'destroy':
		command = 'destroyVirtualMachine'
	else:
		return "Bad command"
	runvm_id = []
	request =  { 'command': 'listVirtualMachines', 'response': 'json'}
	api = CloudServer(api_url, apikey, secret)
	api_response = api.request(request)['listvirtualmachinesresponse']
	
	#CHECK STOP STATUS AND EXCEPTION
	for vm_data in api_response['virtualmachine']:
		if (cmd == 'stop') and (str(vm_data['id']) not in exception_id) and (vm_data['state'] != 'Stopped'):
			print vm_data['id']
			runvm_id.append(vm_data['id'])
		if (cmd == 'start') and (str(vm_data['id']) not in exception_id) and (vm_data['state'] != 'Running'):
			runvm_id.append(vm_data['id'])
		if (cmd == 'destroy') and (str(vm_data['id']) not in exception_id):
			runvm_id.append(vm_data['id'])
	if not runvm_id:
			log ('Nothing to run')
	else:
	#RUN COMMAND FOR VM IN ID LIST runvm_id
		for id in runvm_id:
			request    = { 'command': str(command), 'id': str(id), 'response': 'json'}
			#write in log file
			message = str( cmd + 'VM iD: ' + str(id) )
			log(message)
			api.request(request)
			#TIMEDELAY
			time.sleep(10)

def main(argv=None):
	url = 'http://smsc.ru/sys/get.php'
	values = {  'get_answers' : '1',
				'login' : 'user',
				'psw' : 'password',
				'hour': '0.1',
				'fmt' : '3'
			 }
	#GET DATA FROM SMS-GATE
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	response = urllib2.urlopen(req)
	data = json.loads(response.read())
	print data
	if not data:
		return 'No message'	
	sms=[]
	for el in data:
		if el['phone'] not in phone_whitelist:
			log('Phone number: ' + el['phone'] + ' is not in whitelist. ' +  'Message: ' + el['message'])
			return "Phone number is not in whitelist"
		if el['message']:
			sms.append(el['message'].lower())
			log('Read message from: ' + el['phone'] + ' with text: ' + el['message'])
		else:
			log('No message')
			return 'No message'
	#GET AND RUN COMMAND
	sms_cmd = sms[0]
	print sms_cmd
	if sms_cmd  == 'stop':
		sms2api('stop')
	elif sms_cmd == 'start':
		sms2api('start')
	elif sms_cmd == 'destroy':
		sms2api('destroy')
	else:
		log('Bad command' + sms_cmd)

if __name__ == "__main__":
	sys.exit(main())
