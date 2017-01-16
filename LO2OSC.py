import OSC
import socket
import sys
import errno
import binascii

class LO2OSC(object):

    @staticmethod
    def set_log(func):
        LO2OSC.log_message = func

    @staticmethod
    def release_attributes():
        LO2OSC.log_message = None


    def __init__(self,parent, remotehost = '127.0.0.1', remoteport=9000, localhost='127.0.0.1', localport=9001):
        self.parent = parent
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)

        self._local_addr = (localhost, localport)
        self._remote_addr = (remotehost, remoteport)
        
        self._socket.bind(self._local_addr)
        self.log_message('LiveOSC2 starting on: ' + str(self._local_addr) + ', remote addr: '+ str(self._remote_addr))

        self._callback_manager = OSC.CallbackManager(self)
        self._callback_manager.add('/live/set_peer', self._set_peer)
        
        self.parent = None


    def send(self, address, msg):
        oscmsg = OSC.OSCMessage(address, msg)
        succ = self._socket.sendto(oscmsg.getBinary(), self._remote_addr)
        self.log_message(str(succ) + 'sent ' + str(self._remote_addr) + ':' + str(address) + '=' + str(msg))

    def send_message(self, message):
        self._socket.sendto(message.getBinary(), self._remote_addr)
    
    def hexReturn(self,bytes):
        """Useful utility; prints the string in hexadecimal"""
        strBuild = ""
        #hexbytes = binascii.hexlify(bytes)
        for i in range(len(bytes)):
            #strBuild += "%2x " % (ord(bytes[i]))
            #strBuild = ''.join(chr(int(hexbytes[i:i+2], 16)) for i in range(0, len(hexbytes), 2))
            try:
                int(bytes[i])
                strBuild += str(int(bytes[i]))
            except:
                strBuild += chr(bytes[i])
            #if (i+1) % 8 == 0:
            #    strBuild += repr(bytes[i-7:i+1])

        #if(len(bytes) % 8 != 0):
        #    strBuild += string.rjust("", 11), repr(bytes[i-7:i+1])
        
        return strBuild
    
    def process(self,parent):
        self.parent = parent
        try:
            while 1:
                
                #try:
                self._data, self._addr = self._socket.recvfrom(65536)
                #except self._socket.error:
                #    self.log_message('socket error')
                #    if (10035 == self._socket.error.args[0]):
                #        raise NoData
                try:
                    self._callback_manager.handle(self._data, self._addr)
                    #self.log_message('OSC: ',str(self._data), self._addr)
                except Exception, e:
                    self.log_message('LiveOSC A: error handling message ' + str(e) + "\n" + str(self._data))
                    self.send('/live/error', (str(sys.exc_info())))
                              
        except Exception, e:
            #self.log_message('LiveOSC: Error: '+str(e))
            err, msg = e
            if err != errno.EAGAIN and err != errno.WSAEWOULDBLOCK and err != errno.WSAECONNRESET:
                self.log_message('LiveOSC B: error handling message ' + str(err) + '=' + str(msg))



    def shutdown(self):
        self._socket.close()


    def _set_peer(self, msg, source):
        host = msg[2]
        if host == '':
            host = source[0]
        port = msg[3]
        self.log_message('LiveOSC2: reconfigured to send to ' + host + ':' + str(port))
        self._remote_addr = (host, port)
        