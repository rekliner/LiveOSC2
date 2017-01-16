from _Framework.SessionComponent import SessionComponent
from _Framework.SceneComponent import SceneComponent

from LO2SceneComponent import LO2SceneComponent
from LO2Mixin import LO2Mixin, wrap_init

class LO2SessionComponent(SessionComponent, LO2Mixin):
    #self.parent = parent
    scene_component_type = LO2SceneComponent
    
    @wrap_init
    def __init__(self, c_instance = None, *args, **kwargs):
        self._scene_count = -1
        self._scenes_count = 0
        super(LO2SessionComponent, self).__init__(*args, **kwargs)
        self.__c_instance = c_instance
        #self._selected_scene.disconnect()
        #self._selected_scene = None
        self._selected_scene.set_is_enabled(False)
        
        self._reassign_scenes()
        
        self.add_callback('/live/scene/name/block', self._scene_name_block)
        self.add_callback('/live/clip/name/block', self._clip_name_block)
        self.add_callback('/live/track/name/block', self._track_name_block)
        self.add_callback('/live/track/input/block', self._track_input_block)
        self.add_callback('/live/clip/delete/all', self._delete_all_clips)
        self.add_callback('/live/midi/note', self._midi_note)
        self.add_callback('/live/midi/cc', self._midi_cc)
        self.add_callback('/live/midi/controller', self._midi_cc)
        self.add_callback('/live/midi/pgm', self._midi_pgm)
        self.add_callback('/live/midi/program', self._midi_pgm)

        self.add_function_callback('/live/scenes', self._lo2_on_scene_list_changed)

    
    def send_midi(self, midi_event_bytes):
        """Script -> Live
        Use this function to send MIDI events through Live to the _real_ MIDI devices
        that this script is assigned to.
        """
        self.log_message("midibytes",midi_event_bytes)
        self.__c_instance.send_midi(midi_event_bytes)
        
    def _create_scene(self):
        #obj = SceneComponent if self._scene_count == -1 else self.scene_component_type
        sc = self.scene_component_type(num_slots=self._num_tracks, tracks_to_use_callback=self.tracks_to_use, id=self._scene_count)
        
        self._scene_count += 1
        return sc
    
    
    def on_scene_list_changed(self):
        self._reassign_scenes()
    
    
    def _reassign_scenes(self):
        self.log_message('reassigning scenes')
        diff = len(self.song().scenes) - len(self._scenes)
        
        if diff > 0:
            for i in range(diff):
                self._scenes.append(self._create_scene())
        
        if diff < 0:
            for i in range(len(self._scenes)-1, len(self.song().scenes)-1, -1):
                self._scene[i].disconnect()
                self._scene.remove(self._scene[i])
        
        for i,sc in enumerate(self._scenes):
            sc.set_scene(self.song().scenes[i])

    
    
    # Listeners
    def _lo2_on_scene_list_changed(self):
        if len(self.song().scenes) != self._scenes_count:
            self.send('/live/scenes', len(self.song().scenes))
            self._scenes_count = len(self.song().scenes)


    def _lo2_on_selected_scene_changed(self):
        idx = list(self.song().scenes).index(self.song().view.selected_scene)
        self.send('/live/scene/select', idx)



    # Scene Callbacks
    def _scene_name_block(self, msg, src):
        """ Gets block of scene names
        """
        b = []
        for i in range(msg[2], msg[2]+msg[3]):
            if i < len(self._scenes):
                s = self.scene[i]
                b.append(i, s.scene_name)
            else:
                b.append(i, '')

        self.send('/live/scene/name/block', b)
    
    
    def _scene_selected(self, msg, src):
        """  Selects a scene to view
            /live/scene/selected (int track) """
        if self.has_arg(msg):
            if msg[2] < len(self.song().scenes):
                self.song().view.selected_scene = self.song().scenes[msg[2]]
        else:
            idx = list(self.song().scenes).index(self.song().view.selected_scene)
            self.send('/live/scene/selected', idx)





    # Clip Callbacks
    def _clip_name_block(self, msg, src):
        """ Gets a block of clip names
        """
        b = []
        for i in range(msg[2], msg[2]+msg[3]):
            if i < len(self._scenes):
                s = self.scene[i]
                for j in range(msg[4], msg[4]+msg[5]):
                    if j < len(s._clip_slots):
                        c = s.clip_slots(j)
                        b.append(i, j, c.clip_name)
                    else:
                        b.append(i, j, '')
            else:
                b.append(i, j, '')
        
        self.send('/live/clip/name/block', b)

    # Track Callbacks        
        
    def _track_name_block(self, msg, src):
        """
        Gets block of scene names
        """
        fullList = False
        if msg[3] == 0:
            msg[3] = len(self._channel_strips) - msg[2]
            #if msg[2] == 0:
                #self.track_names = []
                #fullList = True
        #b = []
        for i in range(msg[2], msg[2]+msg[3]):
            if i < len(self._channel_strips):
                t = self.channel_strip(i)
                #b.append(t.track_name)
                self.send('/live/track/name', i, t.track_name)
                #if fullList:
                #    self.track_names.append(t.track_name)
            #else:
                #b.append('')
        #self.log_message(self.track_names)
        self.send('/live/track/name/block', b)


    def _track_input_block(self, msg, src):
        """ creates a block of tracks and sets their names if given
        """
        
        try:
            main_track = int(msg[2],10)
        except:
            self.log_message("ib",self.track_id_from_name(msg[2]))
            main_track = self.track_id_from_name(msg[2])
        i = main_track         
        for input_id in msg[3:]:
            i += 1  #for now this relies on group tracks
            self.log_message("input block",i,main_track)

            try:
                input_id = int(input_id)
                if input_id < len(self.song().tracks[i].input_routings):
                    self.log_message("input by #",input_id,self.song().tracks[i].current_input_routing)
                    self.song().tracks[i].current_input_routing = self.song().tracks[i].input_routings[input_id]
            except:
                if 0 <= i < len(self.song().tracks):
                    lc_routes = [str(route_name).lower() for route_name in self.song().tracks[i].input_routings]
                    try:
                        self.log_message("input by name",i,input_id.lower(),lc_routes.index(input_id.lower()),lc_routes)
                        self.song().tracks[i].current_input_routing = self.song().tracks[i].input_routings[lc_routes.index(str(input_id).lower())]
                    except ValueError:
                        self.log_message("input by name: name not found",i,self.song().tracks[i].name,input_id,lc_routes)




    def _delete_all_clips(self, msg, src):
        tn = [track.name.lower() for track in self.song().tracks]
        save_names = [save_name.lower() for save_name in msg[3:]]
        self.log_message("save names:",save_names,msg)
        for scene in self.song().scenes:
            if not scene.is_empty:
                for clipslot in scene.clip_slots:
                    if clipslot.has_clip and str(clipslot.canonical_parent.name).lower() not in save_names:
                        clipslot.delete_clip()
                        self.log_message("deleting clip",clipslot.canonical_parent.name,"#",scene.name)
                        
    def _midi_pgm(self, msg, src):
        midi_pgm = int(msg[2])
        midi_ch = 1
        if len(msg) > 3:
            midi_ch = int(msg[3])
        midi_msg = (191 + midi_ch, midi_pgm)
        self.log_message("midi_msg",midi_msg)
        self.send_midi(midi_msg)

    def _midi_cc(self, msg, src):
        midi_cc = int(msg[2])
        cc_val = 127
        try:
            cc_val = int(msg[3])
        except:
            pass
        midi_ch = 1
        if len(msg) > 4:
            midi_ch = int(msg[len(msg) - 1])
        midi_msg = (175 + midi_ch, midi_cc, cc_val)
        self.log_message("midi_msg",midi_msg)
        self.send_midi(midi_msg)

    def _midi_note(self, msg, src):
        note_dict = {
            "c" : 0,
            "c#" : 1,
            "db" : 1,
            "d" : 2,
            "d#" : 3,
            "eb" : 3,
            "e" : 4,
            "f" : 5,
            "f#" : 6,
            "gb" : 6,
            "g" : 7,
            "g#" : 8,
            "ab" : 8,
            "a" : 9,
            "a#" : 10,
            "bb" : 10,
            "b" : 11 
        }
        
        try:
            midi_note = int(msg[2])
        except ValueError:
            try:
                octave = int(msg[2][-1])
                msg[2] = msg[2][0:-1]
            except ValueError:
                octave = 0
            midi_note = note_dict[msg[2].lower()] + octave * 12
        midi_ch = 1
        note_vel = 127
        if len(msg) > 3:
            note_vel = int(msg[3])
            if len(msg) > 4:
                midi_ch = int(msg[4])
        midi_msg = (143 + midi_ch, midi_note, note_vel)
        self.log_message("midi_msg",midi_msg)
        self.send_midi(midi_msg)

    def _mid_rec_quant(self, msg, src):
        AVAILABLE_QUANTIZATION = [Live.Song.Quantization.q_no_q,
         Live.Song.Quantization.q_8_bars,
         Live.Song.Quantization.q_4_bars,
         Live.Song.Quantization.q_2_bars,
         Live.Song.Quantization.q_bar,
         Live.Song.Quantization.q_quarter,
         Live.Song.Quantization.q_eight,
         Live.Song.Quantization.q_sixtenth]
 
        self.song().midi_recording_quantization = Live.Song.RecordingQuantization.rec_q_eight
        self._update_quantization_state()