from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.SubjectSlot import subject_slot


from LO2Mixin import LO2Mixin


class LO2ControlElement(ControlSurfaceComponent, LO2Mixin):

    def __init__(self, c_instance):
        self.__c_instance = c_instance
        super(LO2ControlElement, self).__init__()

"""
    def build_midi_map(self, midi_map_handle):
        script_handle = self.__c_instance.handle()
        channel = 15
        for cc in [99,98,97,96,95]: #im reserving these CCs on channel 16.  they're mine. You can't have them.
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, channel, cc)

    def receive_midi(self, midi_bytes):
        self.log_message("cc in!",midi_bytes,midi_bytes[0] & 240,CC_STATUS)
        if midi_bytes[0] & 240 == CC_STATUS:
            channel = midi_bytes[0] & 15
            cc_no = midi_bytes[1]
            cc_value = midi_bytes[2]
    
"""