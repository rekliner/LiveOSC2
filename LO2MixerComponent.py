from _Framework.MixerComponent import MixerComponent

from LO2ChannelStripComponent import LO2ChannelStripComponent
from LO2Mixin import LO2Mixin, wrap_init
#import Live

class LO2MixerComponent(MixerComponent, LO2Mixin):

    @wrap_init
    def __init__(self,parent,c_instance, *a, **kw):
        self.parent = parent
        self.__c_instance = c_instance
        self._track_count = 0
        
        super(LO2MixerComponent, self).__init__(12, 12, *a, **kw)

        self.add_callback('/live/track/create/block', self._track_create_block)

        self.add_function_callback('/live/tracks', self._lo2_on_track_list_changed)
        self._selected_strip.set_track(None)
        self._selected_strip.set_is_enabled(False)

        self._register_timer_callback(self._update_mixer_vols)
        
        self.add_callback('/live/cc/assign', self.parent.cc_assign)
        self.add_callback('/live/cc/clear', self.parent.cc_clear)
        
    def _update_mixer_vols(self):
        pass



    def _create_strip(self):
        return LO2ChannelStripComponent(self,self.__c_instance)


    def _reassign_tracks(self):
        self.log_message('reassigning tracks',len(self.tracks_to_use()),len(self._channel_strips))
        diff = len(self.tracks_to_use()) - len(self._channel_strips)

        if diff > 0:
            for i in range(diff):
                self._channel_strips.append(self._create_strip())

        if diff < 0:
                for i in range(len(self._channel_strips)-1, len(self.tracks_to_use())-1, -1):
                    self._channel_strips[i].disconnect()
                    self._channel_strips.remove(self._channel_strips[i])

        for i,cs in enumerate(self._channel_strips):
            cs.set_track(self.tracks_to_use()[i])
            self.log_message("enumerating",i)


        for i,r in enumerate(self._return_strips):
            if i < len(self.song().return_tracks):
                r.set_track(self.song().return_tracks[i])
            else:
                r.set_track(None)
                
        #self.parent.cc_remap()  #not working...not finding tracks.  stumped.  will it work without reassigning when tracks change?

    def _lo2__on_return_tracks_changed(self):
        self._reassign_tracks()

    # Callbacks
    def _lo2_on_track_list_changed(self):
        if len(self.song().tracks) != self._track_count:
            self.log_message('/live/tracks:' + str(len(self.song().tracks)))
            self.send('/live/tracks', len(self.song().tracks))
            self._track_count = len(self.song().tracks)


    def _lo2_on_selected_track_changed(self):
        id, type = self.track_id_type(self.song().view.selected_track)

        self.send('/live/track/select', type, id)



    # Track Callbacks
    def _track_create_block(self, msg, src):
        """ creates a block of tracks and sets their names if given
        """
        
        try:
            main_track = int(msg[2],10)
        except:
            main_track = self.track_id_from_name(msg[2])
        
        new_tracks = {
            'midi' : 0,
            'audio' : 0
        }
        #track_types = ['midi','audio']
        for track_type in new_tracks:    
            new_tracks[track_type] = 0
            if str(msg[3]).lower() == track_type.lower():
                new_tracks[track_type] = msg[4]
            if len(msg) >= 7:
                if str(msg[5]).lower() == track_type.lower():
                    new_tracks[track_type] = msg[6]

        try:
            names = msg[msg.index('names') + 1:] #case sensitive?
        except:
            names = []
        changed = False    
            
        if main_track == -1:
            self.song().create_audio_track(0) #maybe at end?
            main_track = 0
            self.song().tracks[main_track].name = msg[2]
            changed = True
            
        #self.song().tracks[main_track].is_foldable = 1 #come on ableton, no creating groups in the api?

        self.log_message("names",names)
        if self.song().tracks[main_track].is_foldable:  #count the tracks under this group
            i = 0
            while main_track+i+1 < len(self.song().tracks) and self.song().tracks[main_track+i+1].is_grouped:
                i+=1
            group_tracks = i
            #total_tracks = len(self.song().visible_tracks)
            #self.song().tracks[main_track].fold_state = 1
            #group_tracks = total_tracks - len(self.song().visible_tracks)
            #self.song().tracks[main_track].fold_state = 0
            self.log_message("group tracks:",group_tracks)
            #count tracks
        self.log_message("checking midi under",self.song().tracks[main_track].name,new_tracks['midi'])
        count = 0
        for i in range(new_tracks['midi']):
            if self.song().tracks[main_track+i+1].has_audio_input:
                changed = True
                self.log_message("inserting midi at:",main_track+i+1)
                self.song().create_midi_track(main_track + 1)
                count += 1
                
        for i in range(group_tracks - new_tracks['midi']): #kill any extra midis
            self.log_message("midi at:",main_track,main_track+new_tracks['midi']+i)
            if not self.song().tracks[main_track+new_tracks['midi']+1].has_audio_input:
                self.log_message("extra midi at:",main_track+new_tracks['midi']+i+1)
                changed = True
                self.song().delete_track(main_track+new_tracks['midi'] + 1)
                group_tracks -= 1
            else:
                break
                
        if (group_tracks + count) == new_tracks['midi'] :
                self.song().create_midi_track(main_track + 1) #workaround: if only midi tracks are present, add one more to extend group and delete it later
                changed = True
                
        for i in range(new_tracks['audio']):
            self.log_message("checking audio under",self.song().tracks[main_track].name,new_tracks['audio'],i,main_track+i+1+new_tracks['midi'])
            if (main_track+i+1+new_tracks['midi'] < len(self.song().tracks)) and (not self.song().tracks[main_track+i+1+new_tracks['midi']].has_audio_input) or (main_track+i+1+new_tracks['midi']) > main_track+group_tracks:
                self.log_message("inserting audio at:",main_track+i+1+new_tracks['midi'])
                self.song().create_audio_track(main_track + new_tracks['midi'] + 1)
                changed = True

        self.log_message("updating names")
        for i in range(len(names)):
            #self.log_message("updating names",i,len(names),self.song().tracks[main_track + i + 1].name.lower() , names[i].lower())
            if i < new_tracks['audio'] + new_tracks['midi'] and self.song().tracks[main_track + i + 1].name.lower() != names[i].lower():
                self.song().tracks[main_track + i + 1].name = names[i]
                changed = True
                
        
        if self.song().tracks[main_track].is_foldable:
            #cleanup extra tracks if the main track was a group track
            i = 0
            while main_track+i+1 < len(self.song().tracks) and self.song().tracks[main_track+i+1].is_grouped:
                i+=1
            group_tracks = i
            excess_tracks = group_tracks - (new_tracks['audio'] + new_tracks['midi'])
            self.log_message("cleaning up:",excess_tracks)
            if excess_tracks > 0:
                changed = True
                for i in range(excess_tracks):
                    self.song().delete_track(main_track + group_tracks - i)
                    
                    
        for i in range(new_tracks['audio'] + new_tracks['midi'] + 1): #reset volumes & mutes
            if self.song().tracks[main_track+i].has_audio_input:
                self.song().tracks[main_track+i].mixer_device.volume.value = .85
            self.song().tracks[main_track+i].mute = 0

        #if changed:
        #    self._reassign_tracks()  #i think listeners will handle this just fine
        
        
