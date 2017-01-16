from __future__ import with_statement
from _Framework.ControlSurface import ControlSurface

from LO2SessionComponent import LO2SessionComponent
from LO2MixerComponent import LO2MixerComponent
from LO2TransportComponent import LO2TransportComponent
#from LO2ControlElement import LO2ControlElement

from LO2Mixin import LO2Mixin
from LO2OSC import LO2OSC
import Live
import MidiMap
from threading import Timer



class LiveOSC2(ControlSurface):


    def __init__(self, c_instance):
        self.__c_instance = c_instance
        super(LiveOSC2, self).__init__(c_instance)
        self.send_status = True #mutes track and clip osc output of status

        self._midi_map_handle = None
        self.assigned_ccs = {}
        with self.component_guard():
            LO2OSC.set_log(self.log_message)
            self.osc_handler = LO2OSC(self)
            
            LO2Mixin.set_osc_handler(self.osc_handler)
            LO2Mixin.set_log(self.log_message)
            
#            self._mixer = LO2MixerComponent(self,c_instance)
#            self._session = LO2SessionComponent(c_instance,1,1)
#            self._session.set_mixer(self._mixer)
#            self._transport = LO2TransportComponent(self)
#            self._control = LO2ControlElement()
            
            self.parse()

        #self._mixer.populate_track_names()
        self.show_message('LiveOSC2 loaded')
        self.osc_handler.send('/live/startup', 1) #send sync?
        
        self.add_callback('/live/track/send', self._send)
        
    def _send(self, msg, src):
        self.log_message("send:",self.song().tracks[msg[2]].name,self.song().tracks[msg[2]].mixer_device.sends[msg[3]].value,msg)
        self.song().tracks[msg[2]].mixer_device.sends[msg[3]].value = msg[4]
            

    def disconnect(self):
        self.osc_handler.shutdown()


    def parse(self):
        self.osc_handler.process(self)
        self.schedule_message(1, self.parse)
        
    def cc_clear(self, msg, src):
        self.log_message("clear ccs", msg)
        self.assigned_ccs = {}

    def cc_remap(self):
        self.log_message("remap cc",self.assigned_ccs)
        for key,mapping in self.assigned_ccs.items():
            track_obj = self._mixer.track_obj_from_name(mapping[1])
            self.log_message("tr", track_obj,track_obj._track.name)
            device_obj = track_obj._devices[0].device_obj_from_name(mapping[2])
            self.log_message("dev", device_obj, device_obj._device.name)
            param_obj = device_obj.parameter_obj_from_name(mapping[3])
            self.log_message("prm",  param_obj)
            self.assigned_ccs[key][0] = param_obj
            self.log_message("new ccs",self.assigned_ccs)

    def cc_assign(self, msg, src):
        self.log_message("assign cc", msg)
        self.log_message("devprm", self._mixer._channel_strips[0]._devices[0])
        channel = 15
        #if (msg[2]) in self.assigned_ccs.keys():
        #track_object = LO2Mixin.track_id_from_name(msg[3])
        track_obj = self._mixer.track_obj_from_name(msg[3])
        self.log_message("tr", track_obj,track_obj._track.name)
        device_obj = track_obj._devices[0].device_obj_from_name(msg[4])
        self.log_message("dev", device_obj, device_obj._device.name)
        
        param_obj = device_obj.parameter_obj_from_name(msg[5])
        self.log_message("prm",  param_obj)
        self.assigned_ccs[int(msg[2])] = [param_obj,msg[3],msg[4],msg[5]]
        self.log_message("ccs",self.assigned_ccs)
        Live.MidiMap.forward_midi_cc(self.__c_instance.handle(), self._midi_map_handle, channel, int(msg[2]))

    def build_midi_map(self, midi_map_handle):
        self.log_message("midi map")
        self._midi_map_handle = midi_map_handle
        script_handle = self.__c_instance.handle()
        channel = 15
        #for channel in range(16):
        for cc in range(90,100): #im reserving these CCs on channel 16.  they're mine. You can't have them.
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, channel, cc)

    def receive_midi(self, midi_bytes):
        if midi_bytes[0] & 240 == 176:
            #self.log_message("cc in! ch",midi_bytes[0] & 15,"s",midi_bytes[0] & 240,"msg",midi_bytes)
            channel = midi_bytes[0] & 15
            cc_no = midi_bytes[1]
            cc_value = midi_bytes[2]
            
            if cc_no in self.assigned_ccs.keys():
                self.log_message("acc",midi_bytes,self.assigned_ccs[cc_no])
                po = self.assigned_ccs[cc_no][0]
                po.value = ((po.max - po.min) * float(cc_value / 127.0)) + po.min
                #self.song().tracks[0].devices[0].parameters[1].value = float(cc_value / 127.0)
                #lookup track id (only at assignment?), device id and param id. perhaps can be cached/updated by on_param_changed/dev/tr                
            if channel == 15 and cc_value > 63:
                if cc_no == 64:
                    #self.osc_handler.send('/livescript/next', 1)
                    #repeat the message forward on channel 1
                    #channel = 1
                    midi_msg = (175 + channel, cc_no, cc_value)
                    self.log_message("fwd midi_msg",midi_msg)
                    self.send_midi(midi_bytes)
                elif cc_no == 99:
                    self.osc_handler.send('/livescript/next', 1)
                elif cc_no == 98:
                    self.osc_handler.send('/livescript/undo/redo', 1)
                elif cc_no == 97:
                    self.osc_handler.send('/livescript/undo/all', 1)
                elif cc_no == 96:
                    self.osc_handler.send('/livescript/undo', 1)
                elif cc_no == 95:
                    self.osc_handler.send('/livescript/reload', 1)
                    
    def fade_cb(self,id,final_volume,delta,sec_fade_time,increments,cur_increment,orig_vol):
        #this callback wont persist if run from the channelstrip or mixer component 
        #self.log_message("fade cb:",id,final_volume,delta,sec_fade_time,increments,cur_increment,orig_vol) 
        #f = open('C:\Users\Stage\Documents\cklog.txt','a')
        #f.write(" fade=" + str([id,final_volume,delta,sec_fade_time,increments,cur_increment])+'\n') # python will convert \n to os.linesep
        #f.close() # you can omit in most cases as the destructor will call it                    

        if (delta > 0 and self.song().tracks[id].mixer_device.volume.value < final_volume) or (delta < 0 and self.song().tracks[id].mixer_device.volume.value > final_volume):
            if self.song().tracks[id].mixer_device.volume.value + delta > 1.0:
                self.song().tracks[id].mixer_device.volume.value = 1.0
            elif self.song().tracks[id].mixer_device.volume.value + delta <= 0.0 or cur_increment < 2:
                self.song().tracks[id].stop()
                self.song().tracks[id].mixer_device.volume.value = orig_vol  #if its faded completely out stop the track and put the volume back where it started
            else:
                self.song().tracks[id].mixer_device.volume.value += delta
                cur_increment -= 1
                #self.log_message("fade cb2:",self,id,self.song().tracks[id].mixer_device.volume.value ,final_volume,delta,sec_fade_time,increments,cur_increment) #im stuck, this wont log
                Timer(sec_fade_time / increments, self.fade_cb,[id,final_volume,delta,sec_fade_time,increments,cur_increment,orig_vol]).start() 
            