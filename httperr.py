"""
Test script to handle wierd hhtp errors from radio stationSelect

This describes how to create a hnadler -... https://docs.python.org/3.0/library/urllib.request.html?highlight=urlopen#urllib.request.urlopen

"""
from urllib.request import urlopen, Request

URL = 'http://5.152.208.98:8058'


# try:
# 	file_type = urlopen( URL ).info()['Content-Type']
# 	if 'audio' in file_type:
# 		print("Type = %s" % file_type[6:])
# 	else:
# 		print("MPD: source_type: %s" % file_type)
#
# except Exception as e:
# 	print("MPD: source_type: failed: %s : url: %s" % (e, URL))



#!/usr/bin/env python

stream_url = 'http://94.23.222.12:8027/amysfmspiritofsoul'
request = Request(stream_url)
# try:
request.add_header('Icy-MetaData', 1)
response = urlopen(request)
print(response.info())
icy_metaint_header = response.headers.get('icy-metaint')
if icy_metaint_header is not None:
    metaint = int(icy_metaint_header)
    read_buffer = metaint+255
    content = response.read(read_buffer)
    # title = content[metaint:].split("'")[1]
    # print (title)
# except:
#     print ('Error')
