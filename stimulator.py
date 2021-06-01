# -*- coding: utf-8 -*-
#
# --- Import the libraries
#

import serial
import glob
import sys

#UART class for communication through the UART interface
class UART:
	def __init__(self, port_name, baud_rate, timeout):
		self.port = serial.Serial()
		self.port.port = port_name
		self.port.baudrate = baud_rate
		self.port.timeout = timeout

	def port_name(self, portname):
		self.port.port = portname
		
	def open_port(self):
		self.port.open()
		print("port opened")

	def send(self, data):
		self.port.write(data.encode('latin'))
		print(data.encode('latin'))
		print("message sent")

	def receive(self, length):
		raw = self.port.read(length)	
		print(raw)
		b = raw.decode('latin')
		words = b.split()
		c = int(words[14])
		return c

	def configure(self, new):
		self.port.close()
		self.port.timeout = new
		self.port.open()

	def close_port(self):
		self.port.close()

