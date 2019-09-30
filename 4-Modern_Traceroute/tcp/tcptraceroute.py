#!/usr/bin/env python2
# Copyright (c) 2019, Gouasmia Zakaria
# All rights reserved.


import argparse
import sys
import struct
import socket
import time


def main():
	if len(sys.argv) < 2:
		usage()
		sys.exit(1)

	target = sys.argv[1]
	port = 80
	n = False
	timeout = 3
	maxhops = 30

	if len(sys.argv) >= 3:
		port = int(sys.argv[2])
	if len(sys.argv) >= 4:
		if sys.argv[3].lower() == "true":
			n = True
	if len(sys.argv) >= 5:
		timeout = int(sys.argv[4])
	if len(sys.argv) >= 6:
		maxhops = int(sys.argv[5])

	tcptraceroute(target, port, n, timeout, maxhops)


def usage():
	print "usage: %s target [port [n [timeout [maxhops]]]]" % sys.argv[0]
	print "default:\tport: 80"
	print "\t\tn: False"
	print "\t\ttimeout: 3"
	print "\t\tmaxhops: 30"
	print "examples:\t%s google.com" % sys.argv[0]
	print "\t\t%s 8.8.8.8 80 True 5 20" % sys.argv[0]



def tcptraceroute(target, port, n, timeout, maxhops):
	try:
		ip_target = socket.gethostbyname(target)
	except socket.error as e:
		print "Socket error: %s" % e
		sys.exit(1)

	print "traceroute (%s) to %s (%s), port %d, %d hops max" % ("TCP", target, ip_target, port, maxhops)

	for ttl in range(1, maxhops):
		# s1 is the sender, s2 is the receiver
		s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s1.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
		s1.settimeout(timeout)

		s2 = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
		s2.settimeout(timeout)
		s2.bind(("0.0.0.0", port))

		try:
			# connect is enough; don't need to send anything
			s1.connect((ip_target, port))
		except socket.timeout as e:
			output(ttl)
			continue
		except socket.error as e:
			if e.errno == socket.errno.ECONNREFUSED:
				# Connection refused, which means target was reached
				output(ttl, ip_target, n, "closed")
				break

			# retrieve "Destination unreabable" packet
			try:
				data, addr = s2.recvfrom(1024)
				ip_hop = addr[0]
			except socket.error as e:
				# received nothing
				ip_hop = ""
			if ip_hop:
				output(ttl, ip_hop, n)
			else:
				output(ttl)
			continue
		finally:
			s1.close()
			s2.close()

		output(ttl, ip_target, n, "open")
		break



def output(ttl, ip = "", n = False, status = ""):
	if ip:
		if n:
			reversename = getreversename(ip)
		else:
			reversename = ip
		if status:
			print "%d: %s (%s) [%s]" % (ttl, reversename, ip, status)
		else:
			print "%d: %s (%s)" % (ttl, reversename, ip)
	else:
		print "%d: ***" % (ttl)


def getreversename(ip):
	try:
		name, alias, addresslist = socket.gethostbyaddr(ip)
		return name
	except:
		return ip

if __name__ == "__main__":
	main()
