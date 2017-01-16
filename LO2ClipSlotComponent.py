import Live
from threading import Timer

from _Framework.ClipSlotComponent import ClipSlotComponent
from _Framework.SubjectSlot import subject_slot

from LO2Mixin import LO2Mixin, wrap_init


class LO2ClipSlotComponent(ClipSlotComponent, LO2Mixin):

    def with_clip(fn):
        def wrap(self, *a, **kw):
            if self._clip_slot is not None:
                if self._clip_slot.has_clip:
                    fn(self, *a, **kw)

        return wrap
    
    
    @wrap_init
    def __init__(self, tid, sid, *a, **k):
        self._track_id = tid
        self._scene_id = sid
        
        super(LO2ClipSlotComponent, self).__init__(*a, **k)
    
        self.set_default('_track_id', '_scene_id')
    
        #callbacks = {'color': 'color', 'name': 'name', 'warping': 'warping', 'looping': 'looping', 'loopstart': 'loop_start', 'loopend': 'loop_end', 'start': 'start_marker', 'end': 'end_marker', 'loopjump': 'loop_jump'}
        #for n,p in callbacks.iteritems():
        #   self.add_simple_callback('/live/clip/'+n, '_clip_slot.clip', p, self._is_clip, getattr(self, '_on_clip_'+n+'_changed'))
    
        self.add_callback('/live/clip/play', self._play)
        self.add_callback('/live/clip/rec', self._rec)
        self.add_callback('/live/clip/record', self._rec)
        self.add_callback('/live/clip/stop', self._stop)
        self.add_callback('/live/clip/pitch', self._pitch)
        self.add_callback('/live/clip/select', self._view)
        self.add_callback('/live/clip/double', self._double)
        self.add_callback('/live/clip/loop/end', self._loop_end)
        self.add_callback('/live/clip/loop/start', self._loop_start)
        self.add_callback('/live/clip/looping', self._looping)
        self.add_callback('/live/clip/delete', self._delete)



    def _lo2__update_clip_property_slots(self):
        clip = self._clip_slot.clip if self._clip_slot else None
        
        self._on_clip_name_changed.subject = clip
        self._on_clip_warping_changed.subject = clip
        self._on_clip_looping_changed.subject = clip
        self._on_clip_loopjump_changed.subject = clip
        self._on_clip_loopstart_changed.subject = clip
        self._on_clip_loopend_changed.subject = clip
        self._on_clip_start_changed.subject = clip
        self._on_clip_end_changed.subject = clip
        self._on_clip_gain_changed.subject = clip
    
    
    def _is_clip(self, msg):
        
        if len(msg) >= 4:
            try: 
                int(msg[2])
            except ValueError:
                msg[2] = self.track_id_from_name(msg[2])
                #self.log_message('clip track by name! ' + str(msg[2]) + str(self._track_names))
            return msg[2] == self._track_id and (msg[3] - 1) == self._scene_id


    # Properties
    @property
    def id(self):
        return (self._track_id, self._scene_id)
    
    def _get_name(self):
        if self._clip_slot is not None:
            if self._clip_slot.has_clip:
                return self._clip_slot.clip.name
            else:
                return ''
        else:
            return ''

    #@with_clip
    def _set_name(self, name):
        if self._clip_slot is not None:
            if self._clip_slot.has_clip:
                self._clip_slot.clip.name = name
    
    clip_name = property(_get_name, _set_name)
    
    
    def _get_color(self):
        if self._clip_slot is not None:
            if self._clip_slot.has_clip:
                return self._clip_slot.clip.color
            else:
                return 0
        else:
            return 0

    #@with_clip
    def _set_color(self, color):
            self._clip_slot.clip.name = color
    
    color = property(_get_color, _set_color)

    
    
    # Listeners
    def _lo2__on_clip_state_changed(self):
        self._send_state()
    
    def _lo2__on_clip_playing_state_changed(self):
        self._send_state()
    
    def _send_state(self):
        if self._scene_id == -1:
            return
        
        state = int(self._clip_slot.has_clip) if self._clip_slot is not None else 0
        
        if self._clip_slot.has_clip:
            c = self._clip_slot.clip
            if c.is_playing:
                state = 2
            if c.is_triggered:
                state = 3
        
        self.send('/live/clip/state', self._track_id, self._scene_id, state)

    
    """ #these drive me F*ing crazy
    def _lo2__on_clip_color_changed(self):
        self.send_default('/live/clip/color', self._clip_slot.clip.color)
    
    
    @subject_slot('name')
    def _on_clip_name_changed(self):
        self.send_default('/live/clip/name', self._clip_slot.clip.name)


    @subject_slot('warping')
    def _on_clip_warping_changed(self):
        self.send_default('/live/clip/warping', self._clip_slot.clip.warping)

    @subject_slot('loop_jump')
    def _on_clip_loopjump_changed(self):
        self.send_default('/live/clip/loopjump')

    @subject_slot('looping')
    def _on_clip_looping_changed(self):
        self.send_default('/live/clip/loopstate', self._clip_slot.clip.looping)

    @subject_slot('loop_start')
    def _on_clip_loopstart_changed(self):
        self.send_default('/live/clip/loopstart', self._clip_slot.clip.loop_start)

    @subject_slot('loop_end')
    def _on_clip_loopend_changed(self):
        self.send_default('/live/clip/loopend', self._clip_slot.clip.loop_end)

    @subject_slot('start_marker')
    def _on_clip_start_changed(self):
        self.send_default('/live/clip/start', self._clip_slot.clip.start_marker)

    @subject_slot('end_marker')
    def _on_clip_end_changed(self):
        self.send_default('/live/clip/end', self._clip_slot.clip.end_marker)

    @subject_slot('gain')
    def _on_clip_gain_changed(self):
        self.send_default('/live/clip/gain', self._clip_slot.clip.gain)
    
    """
    
    def __len__(self):
         return 0
         
    # Callbacks
    def _fire(self, msg, src):
        #address, types, trackid, slotid, [delay in seconds]
        if self._clip_slot is not None and self._is_clip(msg):
            self.log_message("firing",msg,src,self._clip_slot)
            if self._clip_slot.has_clip:
                self._clip_slot.clip.fire()
            else:
                self._clip_slot.fire()
                    
    def _play(self, msg, src):
        #address, types, trackid, slotid, [delay in seconds]
        if self._clip_slot is not None and self._is_clip(msg):
            self.log_message("playing",msg,src,self._clip_slot,self._clip_slot.is_playing,self._clip_slot.clip.is_playing)
            if self._clip_slot.has_clip:
                if not self._clip_slot.is_playing:
                    self._clip_slot.clip.fire()
                else:
                    self._clip_slot.clip.position(0) #probably need to quantize
    
    def _rec(self, msg, src):
        #msg format: address, types, trackid, sceneid, 'bars' or 'beats', bars to record
        if self._clip_slot is not None and self._is_clip(msg):
            self.log_message("cliprec:",msg,src,self._clip_slot)
            #f = open('C:\Users\Stage\Documents\cklog.txt','a')
            #f.write(str(msg) + str(self._clip_slot) + str( self._clip_slot.has_clip) + '\n') # python will convert \n to os.linesep
            #f.close() # you can omit in most cases as the destructor will call it            
            autoarm = False
            if self._clip_slot.canonical_parent.arm == 0:
                self._clip_slot.canonical_parent.arm = 1
                #autoarm = True
            if not self._clip_slot.has_clip:
                try:
                    if (msg[4] != 'beats'):
                        msg[5] *= self.song().signature_numerator
                    self._clip_slot.fire(msg[5])
                    
                    if autoarm:
                        secPerBar = self.song().signature_numerator / (self.song().tempo / 60)
                        secToNextBar = (self.song().signature_numerator - (self.song().current_song_time % self.song().signature_numerator)) * secPerBar / self.song().signature_numerator
                        secDelay = (msg[5] / self.song().signature_numerator) * secPerBar + secToNextBar + .01
                        self.log_message('Delay disarm! beats = ',msg[5],"secs=",secDelay, "tempo=",self.song().tempo,"msg=",msg)
                        #for cb in self.callbacks['live/track/arm']:
                        #self._cliparm(['live/track/arm',',ii',msg[2],0])
                        Timer(secDelay, self._cliparm,[['live/track/arm',',ii',msg[2],0],0]).start() #im stuck here, why wont this timer execute?

                        
                        #timer to disable autoarm.
                except:
                    self._clip_slot.fire()
            elif not self._clip_slot.clip.is_playing:
                self._clip_slot.clip.fire()
            else:
                pass
                #restart the clip?  cant be done easily...relies on clip launch mode which i want to keep on toggle...would  double tap work?
                

    def _cliparm(self, msg, src=None):
        self.log_message("arm triggered",msg)
        if self._clip_slot is not None and self._is_clip(msg):
            self.log_message("arm",self._clip_slot.canonical_parent.name, self._clip_slot.canonical_parent.arm, msg)
            self._clip_slot.canonical_parent.arm = msg[3]
            
    def _stop(self, msg, src):
        if self._clip_slot is not None and self._is_clip(msg):
            if self._clip_slot.has_clip:
                self._clip_slot.clip.stop()
            else:
                self._clip_slot.stop()

    def _double(self, msg, src):
        if self._clip_slot is not None and self._is_clip(msg):
            if self._clip_slot.has_clip:
                self._clip_slot.clip.duplicate_loop()

    def _loop_end(self, msg, src):
        if self._clip_slot is not None and self._is_clip(msg):
            if self._clip_slot.has_clip:
                if self._clip_slot.clip.is_playing:
                    #hack to try to keep playing clip in sync while changing loop end
                    self._clip_slot.clip.loop_end = msg[4]
                    self._clip_slot.clip.position = 0 #this will do for now, just execute on the beat
                else:
                    if self._clip_slot.clip.loop_end != msg[4]:  #weird ableton behavior if loopend is set to its current position
                        self._clip_slot.clip.loop_end = msg[4]

    def _loop_start(self, msg, src):
        if self._clip_slot is not None and self._is_clip(msg):
            if self._clip_slot.has_clip:
                if self._clip_slot.clip.loop_start != msg[4]:
                    self._clip_slot.clip.loop_start = msg[4] 

    def _looping(self, msg, src):
        if self._clip_slot is not None and self._is_clip(msg):
            if self._clip_slot.has_clip:
                self._clip_slot.clip.looping = msg[4] 

    def _delete(self, msg, src):
        if self._clip_slot is not None and self._is_clip(msg):
            if self._clip_slot.has_clip:
                self._clip_slot.delete_clip()

    @with_clip
    def _pitch(self, msg, src):
        if self._is_clip(msg):
            c = self._clip_slot.clip
            if len(msg) == 6:
                c.pitch_coarse = msg[4]
                c.pitch_fine = msg[5]
            else:
                self.send_default('/live/clip/pitch', c.pitch_coarse, c.pitch_fine)


    @with_clip
    def _view(self, msg, src):
        if self._is_clip(msg):
            tr = self._clip_slot.canonical_parent
            self.song().view.detail_clip = self._clip_slot.clip
            self.application().view.show_view('Detail/Clip')
            
            if 0:
                self.song().view.selected_track = self._clip_slot.canonical_parent
                self.song().view.selected_scene = self.song().scenes[self._scene_id]


