from _Framework.ChannelStripComponent import ChannelStripComponent
from _Framework.SubjectSlot import subject_slot

from LO2DeviceComponent import LO2DeviceComponent
from LO2ParameterComponent import LO2ParameterComponent
from LO2Mixin import LO2Mixin, wrap_init
from threading import Timer
import Live

class LO2ChannelStripComponent(ChannelStripComponent, LO2Mixin):
    
    @wrap_init
    def __init__(self,parent,c_instance, *a, **kw):
        self.parent = parent
        self.__c_instance = c_instance
        self._track_id = None
        self._type = None
        self._devices = []
        self._sends = []
        
        super(LO2ChannelStripComponent, self).__init__(*a, **kw)
    
        self.set_default('_track_id')
        
        for t in [0, 1]:
            for p in ['mute', 'solo', 'arm']:
                self.add_mixer_callback('/live/'+self._track_types[t]+p, p)
                #self.log_message("callback:",self._track_id,'/live/'+self._track_types[t]+p)
            for p in ['volume', 'panning']:
                self.add_mixer_callback('/live/'+self._track_types[t]+p, p, 1)
                #self.log_message("callback:",self._track_id,'/live/'+self._track_types[t]+p)
                
        #self.add_callback('/live/track/volume',self._vol)
        self.add_mixer_callback('/live/master/volume', 'volume', 1)
        self.add_mixer_callback('/live/master/pan', 'pan', 1)

        self.add_callback('/live/track/send', self._send)
        self.add_callback('/live/track/stop', self._stop)
        self.add_callback('/live/clip/copy', self._copy)
        self.add_callback('/live/track/input', self._input)
        self.add_callback('/live/track/insub', self._insub)
        self.add_callback('/live/track/output', self._output)
        self.add_callback('/live/track/outsub', self._outsub)
        self.add_callback('/live/track/collapsed', self._collapsed)
        self.add_callback('/live/track/foldable', self._foldable)
        self.add_callback('/live/track/fold', self._fold)
        self.add_callback('/live/track/fade', self._fade)

        
        for t in self._track_types:
            self.add_callback('/live/'+t+'crossfader', self._crossfader)
            
        for ty in ['track', 'return']:
            self.add_simple_callback('/live/'+ty+'/name', '_track', 'name', self._is_track, getattr(self, '_lo2__on_track_name_changed'))
            self.add_simple_callback('/live/'+ty+'/color', '_track', 'color', self._is_track, getattr(self, '_on_track_color_changed'))
                    
        self.add_callback('/live/track/state', self._track_state)
        
        for ty in self._track_types:
            self.add_callback('/live/'+ty+'devices', self._device_list)
            self.add_callback('/live/'+ty+'select', self._view)
        
        
    def with_track(fn):
        def decorator(*a, **kw):
            if self._track is not None:
                fn(*a, **kw)
            
        return decorator
            
    @property
    def id(self):
        if self._track is not None:
            return self._track_id
        else:
            return -1


    def _get_name(self):
        if self._track is not None:
            return self._track.name
        else:
            return ''

    def _set_name(self, name):
        if self._track is not None:
            self._track.name = name
    
    track_name = property(_get_name, _set_name)
    
    
    def disconnect(self):
        LO2Mixin.disconnect(self)  
        super(LO2ChannelStripComponent, self).disconnect()
        pass
    
    
    def _is_track(self, msg):
        if 'return' in msg[0]:
            ty = 1
        elif 'master' in msg[0]:
            ty = 2
        else:
            ty = 0
            
        if ty != 2:
            msg[2] = self.track_id_from_name(msg[2])

        check_id = msg[2] == self._track_id if ty != 2 else True
        
        #self.log_message('is track: ',str(msg), ty == self._type  ,   check_id, self._get_name(), self._track_id ,"=", msg[2], "type",self._type )
        
        return ty == self._type and check_id
                     
                          
    def add_mixer_callback(self, addr, property, mixer = 0):
        def cb(msg, src = None):
            if self._is_track(msg) and self.is_enabled():
                sp2 = self.song()
                sp = self.__c_instance.song()
                v = msg[3] if len(msg) == 4 else None
                if sp.tracks[msg[2]] is not None:
                    #obj = getattr(self._track.mixer_device, property) if mixer else self._track
                    obj = getattr(sp.tracks[msg[2]].mixer_device, property) if mixer else sp.tracks[msg[2]]
                    obj2 = getattr(sp2.tracks[msg[2]].mixer_device, property) if mixer else sp2.tracks[msg[2]]
                    pr = 'value' if mixer else property
                    ot = float if mixer else int
                    #f = open('C:\Users\Stage\Documents\cklog.txt','a')
                    #f.write(str(msg) + sp.tracks[msg[2]].name + " mixer=" + str(mixer) + " v=" +str(v) + " p="+str(property) + str(obj)+ str(obj2) +'\n') # python will convert \n to os.linesep
                    #f.close() # you can omit in most cases as the destructor will call it                    
                    if v != None:
                        self.log_message('mixer set' ,sp.tracks[msg[2]].name,ot(v),obj,pr,msg)
                        setattr(obj, pr, ot(v))
                        setattr(obj2, pr, ot(v))
                    else:
                        if self._type == 2:
                            self.send('/live/master/'+property, ot(getattr(obj, pr)))
                        else:
                            self.send_default('/live/'+self._track_types[self._type]+property, ot(getattr(obj, pr)))

        self.add_callback(addr, cb)
                          

    def set_track(self, track):
        if self._is_enabled_ovr:
            self._track_id, self._type = self.track_id_type(track)
            #self.log_message("set track:",self._get_name(),self._track_id,self._type)
            super(LO2ChannelStripComponent, self).set_track(track)
            
            self._on_device_list_changed.subject = track
            self._on_track_color_changed.subject = track
            self._on_track_state_changed.subject = track
            
            m = track.mixer_device if track else None
            self._on_volume_changed.subject = m.volume if track else None
            self._on_panning_changed.subject = m.panning if track else None
            
            self._lo2__on_sends_changed()
            self._on_device_list_changed()

    
    def _lo2__on_sends_changed(self):
        if self._track is not None and self._type != 2:
            diff = len(self._track.mixer_device.sends) - len(self._sends)
            
            if diff > 0:
                for i in range(diff):
                    self._sends.append(LO2ParameterComponent(True))
            
            if diff < 0:
                for i in range(len(self._sends)-1, len(self._track.mixer_device.sends)-1, -1):
                    self._sends[i].disconnect()
                    self._sends.remove(self._sends[i])
            
            for i,s in enumerate(self._sends):
                s.set_parameter(self._track.mixer_device.sends[i])
    


    @subject_slot('devices')
    def _on_device_list_changed(self):
        if self._track is not None:
            diff = len(self._track.devices) - len(self._devices)

            if diff > 0:
                for i in range(diff):
                    self._devices.append(LO2DeviceComponent(self))

            if diff < 0:
                    for i in range(len(self._devices)-1, len(self._track.devices)-1, -1):
                        self._devices[i].disconnect()
                        self._devices.remove(self._devices[i])
        
            for i,dc in enumerate(self._devices):
                dc.set_device(self._track.devices[i])

            #self._send_device_list()
            #self.parent.parent.cc_remap()

    @subject_slot('value')
    def _on_volume_changed(self):
        pass
        #self.log_message('volume change',self._track_id,self._type,self._track,(self._track == self.song().master_track))
        #self.send_default('/live/'+self._track_types[self._type]+'volume', self._track.mixer_device.volume.value)

    @subject_slot('value')
    def _on_panning_changed(self):
        self.send_default('/live/'+self._track_types[self._type]+'panning', self._track.mixer_device.panning.value)

    


    # Callbacks
    def _lo2__on_mute_changed(self):
        if self._type < 2 and self._type is not None:
            self.log_message('mute track',self._track_id,self._track.name,self._type,self,self._track)
            self.send_default('/live/'+self._track_types[self._type]+'mute', self._track.mute)

    def _lo2__on_solo_changed(self):
        if self._type < 2 and self._type is not None:
            self.send_default('/live/'+self._track_types[self._type]+'solo', self._track.solo)

    def _lo2__on_arm_changed(self):
        if self._type == 0 and self._type is not None and self._track.can_be_armed:
            self.send_default('/live/'+self._track_types[self._type]+'arm', self._track.arm)
    
    @subject_slot('playing_slot_index')
    def _on_track_state_changed(self):
        self.send_default('/live/track/state', self._track.playing_slot_index)
    
    
    @subject_slot('color')
    def _on_track_color_changed(self):
        self.send_default('/live/'+self._track_types[self._type]+'color', self._track.color)

            
    def _lo2__on_track_name_changed(self):
        self.send_default('/live/'+self._track_types[self._type]+'name', self._track.name)

    
    @subject_slot('name')
    def _on_track_name_changed(self):
        self.send_default('/live/'+self._track_types[self._type]+'name', self._track.name)

    
    #@with_track
    def _device_list(self, msg, src):
        if self._is_track(msg) and self._track is not None:
            self._send_device_list()


    def _send_device_list(self):
            devices = []
            for i,d in enumerate(self._track.devices):
                devices.append(i)
                devices.append(d.name)
               
            if self._type == 2:
                self.send('/live/'+self._track_types[self._type]+'devices', *devices)
            else:
                self.send_default('/live/'+self._track_types[self._type]+'devices', *devices)


    def _stop(self, msg, src):
        if self._track is not None and self._is_track(msg):
            self.log_message('stop track',self._track_id,msg)
            self._track.stop_all_clips()

    def _input(self, msg, src):
        if self._track is not None and self._is_track(msg):
            try:
                msg[3] = int(msg[3])
                if msg[3] < len(self._track.input_routings):
                    self.log_message("input by #",msg[3],self._track.current_input_routing)
                    self._track.current_input_routing = self._track.input_routings[msg[3]]
            except:
                try:
                    self.log_message("input by name",str(self._track.input_routings))
                    lc_routes = [str(route_name).lower() for route_name in self._track.input_routings]
                    self.log_message("input by name",str(msg[3]).lower(),lc_routes.index(str(msg[3]).lower()),lc_routes)
                    self._track.current_input_routing = self._track.input_routings[lc_routes.index(str(msg[3]).lower())]
                except ValueError:
                    self.log_message("input by name: name not found",msg[3],lc_routes)
                    
            if len(msg) == 5:
                msg.pop(3)
                self.log_message("insub following",msg)
                self._insub(msg,src)
                
            self.log_message("input by name: thats all",msg[3])

    def _insub(self, msg, src):
        if self._track is not None and self._is_track(msg):
            try:
                msg[3] = int(msg[3])
                self.log_message("insub by #",msg[3],self._track.current_input_sub_routing)
                if msg[3] < len(self._track.input_sub_routings):
                    self._track.current_input_sub_routing = self._track.input_sub_routings[msg[3]]
            except:
                lc_routes = [str(route_name).lower() for route_name in self._track.input_sub_routings]
                try:
                    self.log_message("insub by name",str(msg[3]).lower(),lc_routes.index(str(msg[3]).lower()),lc_routes)
                    self._track.current_input_sub_routing = self._track.input_sub_routings[lc_routes.index(str(msg[3]).lower())]
                except ValueError:
                    self.log_message("insub by name: name not found",msg[3],lc_routes)

    def _output(self, msg, src):
        if self._track is not None and self._is_track(msg):
            try:
                msg[3] = int(msg[3])
                self.log_message("output by #",msg[3],self._track.current_output_routing)
                if msg[3] < len(self._track.output_routings):
                    self._track.current_input_routing = self._track.output_routings[msg[3]]
            except:
                lc_routes = [str(route_name).lower() for route_name in self._track.output_routings]
                try:
                    self.log_message("output by name",str(msg[3]).lower(),lc_routes.index(str(msg[3]).lower()),lc_routes)
                    self._track.current_output_routing = self._track.output_routings[lc_routes.index(str(msg[3]).lower())]
                except ValueError:
                    self.log_message("output by name: name not found",self._track.name,msg[3],lc_routes)
                    
            if len(msg) == 5:
                msg.pop(3)
                self.log_message("outsub following",msg)
                self._outsub(msg,src)

    def _outsub(self, msg, src):
        if self._track is not None and self._is_track(msg):
            try:
                msg[3] = int(msg[3])
                self.log_message("outsub by #",msg[3],self._track.current_output_sub_routing)
                if msg[3] < len(self._track.output_sub_routings):
                    self._track.current_output_sub_routing = self._track.output_sub_routings[msg[3]]
            except:
                lc_routes = [str(route_name).lower() for route_name in self._track.output_sub_routings]
                try:
                    self.log_message("outsub by name",msg[3].lower(),lc_routes.index(msg[3].lower()),lc_routes)
                    self._track.current_output_sub_routing = self._track.output_sub_routings[lc_routes.index(msg[3].lower())]
                except ValueError:
                    self.log_message("outsub by name: name not found",msg[3],lc_routes)

    def _copy(self, msg, src):
        if self._track is not None and self._is_track(msg):
            self.log_message('copy clip on track',self._track_id,msg)
            clipslot = msg[3] - 1
            if self._track.clip_slots[clipslot].has_clip:
                self._track.duplicate_clip_slot(clipslot)
            else:
				self.log_message('copy clip not found',self._track_id,msg)

    def _track_state(self, msg, src):
        if self._is_track(msg):
            self._on_track_state_changed()


    def _view(self, msg, src):
        if self._is_track(msg) and self._track is not None:
            self.song().view.selected_track = self.song().tracks[-1] #by selecting the last track beforehand the computer screen shows the selected track on the left
            if len(msg) > 3:
                offset_track = self._track_id + int(msg[3])
                self.song().view.selected_track = self.song().tracks[offset_track]
            else:
                self.song().view.selected_track = self._track
              
            #resetting scene to the first also
            self.song().view.selected_scene = self.song().scenes[-1] #this is necessary since the scene 0 might already be selected but not in view
            self.song().view.selected_scene = self.song().scenes[0]
            


    def _crossfader(self, msg, src):
        if self._is_track(msg) and self._track is not None:
            # Master
            if self._type == 2:
                self._track.mixer_device.crossfader.value = msg[1]
                    
            # Assign xfader
            else:
                self.log_message("xfade ",msg)
                pass
                
    def _collapsed(self, msg, src):
        if self._is_track(msg) and self._track is not None:
            self.log_message("collapsed:",self._track.view.is_collapsed,msg)
            if len(msg) > 3:
                self._track.view.is_collapsed = msg[3]

    def _foldable(self, msg, src):
        if self._is_track(msg) and self._track is not None:
            self.log_message("foldable:",self._track.is_foldable,msg)
            self.send_default(msg[1],self._track.is_foldable)

    def _fold(self, msg, src):
        if self._is_track(msg) and self._track is not None:
            self.log_message("fold:",self._track.fold_state,msg)
            if len(msg) > 3:
                self._track.fold_state = msg[3]
                
    def _send(self, msg, src):
        if self._is_track(msg) and self._track is not None:
            self.log_message("send:",self._track.mixer_device.sends[msg[3]],self._track.mixer_device.sends[msg[3]].value,msg)
            self._track.mixer_device.sends[msg[3]].value = msg[4]
            

    def _fade(self, msg, src):
        if self._is_track(msg) and self._track is not None:
            if msg[4].lower() == "bars":
                sec_fade_time = msg[5] * (self.song().signature_numerator / (self.song().tempo / 60.0))
            elif msg[4].lower() == "beats":
                sec_fade_time = msg[5] * (1 / (self.song().tempo / 60.0))
            else:
                sec_fade_time = float(msg[5])
            increments = 20.0
            if len(msg) > 6:
                increments = float(msg[6])
            delta = float(msg[3]) - self._track.mixer_device.volume.value / increments
            self.log_message("fade:",msg,self._track.mixer_device.volume.value ,sec_fade_time,increments,delta)
            orig_vol = self._track.mixer_device.volume.value
            #unregister callback
            self.parent.parent.fade_cb(self._track_id,msg[3],delta,sec_fade_time,increments,increments,orig_vol)  #this dies if run at the channel level, buggy in mixer object too
            #Timer(sec_fade_time / increments, self.parent.parent.fade_cb,[self._track_id,msg[3],delta,sec_fade_time,increments,increments - 1]).start() 

