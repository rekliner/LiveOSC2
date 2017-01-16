from _Framework.TransportComponent import TransportComponent
from _Framework.SubjectSlot import subject_slot

from LO2Mixin import LO2Mixin

class LO2TransportComponent(TransportComponent, LO2Mixin):


    def __init__(self, parent, *a, **kw):
        self.parent = parent
        super(LO2TransportComponent, self).__init__(*a, **kw)

        s = self.song()
        self._on_metronome_changed.subject = s
        self._on_signature_numerator_changed.subject = s
        self._on_signature_denominator_changed.subject = s
        self._on_tempo_changed.subject = s
        self._on_playing_changed.subject = s
        
    
        self.add_default_callback('/live/tempo', s, 'tempo', float)
        self.add_default_callback('/live/time', s, 'current_song_time', float)
        self.add_default_callback('/live/overdub', s, 'overdub', int)
        self.add_default_callback('/live/metronome', s, 'metronome', int)
    
        self.add_function_callback('/live/cue/next', s.jump_to_next_cue)
        self.add_function_callback('/live/cue/prev', s.jump_to_prev_cue)
        
        self.add_function_callback('/live/play', self.start_playing)
        self.add_function_callback('/live/play/continue', s.continue_playing)
        self.add_function_callback('/live/play/selection', s.play_selection)
        self.add_function_callback('/live/stop', s.stop_playing)
        self.add_function_callback('/live/timesig', self.timesig)
    
        self.add_callback('/live/undo', self._undo)
        self.add_function_callback('/live/redo', s.redo)
    
        
        self.add_callback('/live/track/create', self._add_track);
        self.add_callback('/live/return/create', self._add_return_track);
        self.add_callback('/live/scene/create', self._add_scene);
        self.add_callback('/live/clip/create', self._add_clip);

        self.add_callback('/live/track/delete', self._del_track);
        self.add_callback('/live/return/delete', self._del_return_track);
        self.add_callback('/live/scene/delete', self._del_scene);
        self.add_callback('/live/clip/delete', self._del_clip);

        self.add_callback('/live/controller/position', self._controller_position);
        
    def _undo(self, msg, src):
        undos = 1
        try:
            undos = msg[2]
        except:
            pass
        for i in range(undos):
            self.song().undo()
            
    def start_playing(self):
        self.song().start_playing()
        self.send('/live/sync',self.song().is_playing, self.song().tempo, 0.0, self.song().get_current_beats_song_time().beats, self.song().signature_numerator, self.song().signature_denominator)
        #self.song().current_song_time not relevant since starting over
    # Callbacks
    @subject_slot('metronome')
    def _on_metronome_changed(self):
        self.send('/live/metronome', int(self.song().metronome))

    @subject_slot('signature_numerator')
    def _on_signature_numerator_changed(self):
        self._on_signature_changed()

    @subject_slot('signature_denominator')
    def _on_signature_denominator_changed(self):
        self._on_signature_changed()

    def _on_signature_changed(self):
        self.send('/live/signature', self.song().signature_numerator, self.song().signature_denominator)
        self.send('/live/sync',self.song().is_playing, self.song().tempo, self.song().current_song_time, self.song().get_current_beats_song_time().beats, self.song().signature_numerator, self.song().signature_denominator)
                  
    @subject_slot('tempo')
    def _on_tempo_changed(self):
        self.send('/live/tempo', self.song().tempo)
        self.send('/live/sync',self.song().is_playing, self.song().tempo, self.song().current_song_time, self.song().get_current_beats_song_time().beats, self.song().signature_numerator, self.song().signature_denominator)

    @subject_slot('loop')
    def _on_loop_changed(self):
        self.send('/live/loop', self.song().loop)


    @subject_slot('is_playing')
    def _on_playing_changed(self):
        self.send('/live/play', self.song().is_playing)



    def _add_track(self, msg, src):
        if len(msg) >= 3:
            if msg[2] == 1 or str(msg[2]).lower() == 'midi':
                self.song().create_midi_track(msg[3] if len(msg) >= 4 else 0)
            else:
                self.song().create_audio_track(msg[3] if len(msg) >= 4 else 0)

    def _add_return_track(self, msg, src):
        self.song().create_return_track()

    def _add_scene(self, msg, src):
        self.song().create_scene(msg[2] if len(msg) == 3 else 0)

    
    def _del_track(self, msg, src):
        if len(msg) == 3:
            self.song().delete_track(msg[2])

    def _del_return_track(self, msg, src):
        if len(msg) == 3:
            self.song().delete_return_track(msg[2])

    def _del_scene(self, msg, src):
        if len(msg) == 3:
            self.song().delete_scene(msg[2])


    def _add_clip(self, msg, src):
        if len(msg) >= 4:
            msg[2] = self.track_id_from_name(msg[2])
            if msg[2] < len(self.song().tracks):
                tr = self.song().tracks[msg[2]]
                if msg[3] < len(self.song().scenes):
                    c = tr.clip_slots[msg[3]]
                    if not c.has_clip:
                        if len(msg) == 5:
                            c.create_clip(msg[4])
                        else:
                            c.create_clip()

    def _del_clip(self, msg, src):
        if len(msg) >= 4:
            msg[2] = self.track_id_from_name(msg[2])
            if msg[2] < len(self.song().tracks):
                tr = self.song().tracks[msg[2]]
                if msg[3] < len(self.song().scenes):
                    c = tr.clip_slots[msg[3]]
                    if c.has_clip:
                        self.log_message("deleting clip",msg[2],msg[3])
                        c.delete_clip(msg[3])

    def _controller_position(self, msg, src):
        track_index = self.track_id_from_name(msg[3])
        if len(msg) < 5:
            scene_index = 0
        else:
            scene_index = 0
        if len(msg) == 6:
            track_index += 1
        controller = self.parent._control_surfaces()[msg[2]]
        controller.highlighting_session_component().set_offsets(track_index,scene_index)
        
    def timesig(self,msg,src):
        self.song().signature_numerator = msg[2]
        self.song().signature_denominator = msg[3]
