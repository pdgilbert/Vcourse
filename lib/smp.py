# License GPL 2. Copyright Paul D. Gilbert, 2017
"""Simple message protocol for communication between RC and race boats (BTs)."""

import logging
import socket

BUFFER_SIZE = 1024  # not more than 4 digits

def snd(s, msg) :
    if msg is None : 
          raise RuntimeError("attempt to send empty (None) message.")
    if msg is "" : 
          raise RuntimeError("attempt to send empty message string.")
    # msg should be string. 
    #It gets prepended with the 4 digit length (for rcv) and convert to byte, eg b"ok"
    msg  = (str(len(msg)).zfill(4) + msg).encode()
    tot = len(msg)
    #logging.debug('sending ' + msg.decode() + ' length ' + str(tot))

    t = 0
    while t < tot:
       #logging.debug('msg ' + msg[t:].decode())
       sent = s.send(msg[t:])
       #logging.debug('sent ' + str(sent))
       if sent == 0 :
          raise RuntimeError("socket connection broken")
       t  +=  sent
    return t

def rcv(s):
    chunks  = []
    tot = s.recv(4).decode()
    try:
       tot = int(tot)
    except:
       raise RuntimeError("message length '" + tot +"' does not convert to int.")
    #logging.debug('rcv tot ' + str(tot))

    t = 0
    while t < tot :
       chunk = s.recv(min(tot, BUFFER_SIZE))
       #logging.debug('chunk ' + str(chunk))
       if chunk == b'' : 
          raise RuntimeError("socket connection broken")
       chunks.append(chunk)
       t = t + len(chunk)
    r = (b''.join(chunks)).decode()
    #logging.debug('returning chunks ' + r)
    return  r
