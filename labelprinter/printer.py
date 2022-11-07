#!/usr/bin/env python
from PIL import Image
import sys 
import random
import socket
import os
import tempfile
import subprocess
import cairo
import draw

def get_filename(fn) :
	return os.path.join(os.path.dirname(os.path.realpath(__file__)), fn)

header = list(open(get_filename("header.prn"), "rb").read())

def format_image(img) :
	img = Image.open(img)
	assert(img.width == 128)
	out=list(header)
	for i in range(4) :
		out[0x83+i] = (img.height>>(i*8))&0xff
	randrange=1
	for y in range(img.height) :
		packet = [0x47,16, 0]
		packet.extend((0,)*16)
		
		for x in range(img.width) :
			if img.getpixel((img.width-1-x,y)) == 0 :
				packet [int(x/8)+3] |= (1<<(7-(x&7)))
		out.extend(packet)

	out.append(0x1a)
	return bytes(out)

def getpixel(surf, x, y) :
	offset = surf.get_stride()*y + x*4
	return surf.get_data()[offset] != 0

def format_surface(surf) :
	assert(surf.get_format() == cairo.Format.RGB24)
	assert(surf.get_height() == 128)
	out=list(header)
	for i in range(4) :
		out[0x83+i] = (surf.get_width()>>(i*8))&0xff
	randrange=1
	for y in range(surf.get_width()) :
		packet = [0x47,16, 0]
		packet.extend((0,)*16)
		
		for x in range(surf.get_height()) :
			if getpixel(surf, y, x) == 0 :
				packet [int(x/8)+3] |= (1<<(7-(x&7)))
		out.extend(packet)

	out.append(0x1a)
	return bytes(out)

def print_to_ip(surf ,ip, port=9100) :
	out = format_surface(surf)
	s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((ip, port))
	s.send(out)
	s.close()

if __name__ == "__main__" :
	imgsurf = draw.render_text("ar1-dev-1", "68:f7:28:77:e5:1d", "68:f7:28:77:e5:1d".replace(":", ""), True)
	print_to_ip(imgsurf, 'labelprinter-2.workstation.selfnet.de')
