LiveOSC2
========

Rekliner's version of LiveOSC2 working for Ableton Live 9.6.2. 
Fixed minor bugs in Stu's work, like ignoring socket timeout or disconnect errors and not killing all the track callbacks whenever one is disconnected
    -It wasn't responding to anything under /live/track so I put a bandaid on it in the ChannelStrip disconnect.

As of 9/2016 I added the following features:
* responds to 'k' type tag in OSC as the number of bars (int) in ableton to delay the attached command.  This is just for me and my livescript program.
* if given a string instead of an int to identify the track it tries to match the name.  Tracks can now be referred to without knowing the ID. 
    -Don't name your track a parseable integer like '1' or '250624'
    -Spaces are *sometimes* replaced by dashes within Live, so '1 MIDI' might be referred to as '1-MIDI'..this appears to just be for autonumbering
    -it's case insensitive
    -if there are track name duplicates the first (farthest left) will be used
* added /live/clip/copy to duplicate a clip to the next available slot
* disabled loopjump reporting by default...it annoyed me
* changed /live/clip/play to leave a clip playing if it already was.  This allows play commands to be absolute and not toggle a clip.
* added /live/clip/fire to take the place of the original behavior of /live/clip/play as a toggle for the slot
* added /live/clip/rec or /live/clip/record to start recording on a clip slot or play the clip (not toggle it) if it exists. 
    -supports length of recording in beats
    -automatically arms a disarmed track before recording if necessary (currently hardcoded to do so at the start of the next beat)
* added /live/track/input and /live/track/output to reassign inputs or outputs for a track
    -will search for an input/output by name (case insensitive) if given a string or just use the id if you send an integer
    -sub routing can optionally be tacked on to this command or sent seperately
* added /live/track/insub and /live/track/outsub to reassign input or output sub-routings for a track
    -will also search for an sub-input/sub-output by name if given a string or just use the id if you send an integer.
    -sending it an integer works out well to limit by MIDI channels since 0 is 'all channels'
    -spaces are NOT converted to dashes ex 'Ch. 4'.
*implemented /live/track/collapse
    -this shows or hides a rack within a track
*added /live/track/fold
    -if it is not a group track it returns -1
    -if it is a group track it returns 0 if the subtracks are visible and 1 if they are hidden
    -if sent a 0 or 1 will fold the subtracks




LiveOSC binds to localhost by default receiving OSC on 9000 and sending on 9001
You can change this dyncamically using:
    /live/set_peer <host> <port>

Calls without an argument can be passed the dummy argument 'query' for systems that dont support sending osc messages without arguments.

* Denotes this is sent automatically from Live upon change
<int arg> Optional argument

Song
----

/live/selection (int track_id, int scene_id, int width, int height
    Set the position of the "red ring" in Live


Transport
---------
/live/tempo (float tempo)
    Sets the tempo, no argument returns tempo

/live/time
    Returns the current song time

groove

cue points
set / delete cue

/live/cue/next
/live/cue/prev
    Jumps to the next and previous cue points in arrangement view
    
/live/play
    Starts playing
/live/play/continue
    Restarts playing from the current point
/live/play/select
    Starts playing the current selection in arrangement view


/live/undo
/live/redo

/live/overdub
/live/metronome


/live/loop
/live/signature


Scenes
------
/live/scenes
    Returns the number of scenes in the live set
    
/live/scene/name (int scene_id, <string name>)
    Sets / gets the name for scene_id.
    *** LiveOSC no longer returns all scene names when scene_id is ommitted, use scene/block instead ***
/live/scene/name/block (int scene_id, int height)
    Returns a block of scene names

/live/scene/color (int scene_id, <int color>)
    Sets / gets the color for scene_id.

/live/scene/state (int scene_id)
    Returns the state for scene_id (1 = triggered, 0 = stopped)

/live/scene/select (int scene_id)
    Selects scene_id
    
/live/scene/create (int offset)
    Available in API but not implemented

/live/scene/duplicate (int scene_id)
    Available in API but not implemented

Tracks
------
/live/tracks
    Returns the number of tracks and returns in the live set

/live/track/arm (int track_id, <int state>)
/live/return/arm (int track_id, <int state>)
/live/master/arm (<int state>)
    Sets / gets the arm state of track_id

/live/track/mute (int track_id, <int state>)
/live/return/mute (int track_id, <int state>)
/live/master/mute (<int state>)
    Sets / gets the mute state of track_id

/live/track/solo (int track_id, <int state>)
/live/return/solo (int track_id, <int state>)
/live/master/solo (<int state>)
    Sets / gets the solo state of track_id


/live/track/volume (int track_id, <float volume>)
/live/return/volume (int track_id, <float volume>)
/live/master/volume (<float volume>)
    Sets / gets the mixer volume of track_id

/live/track/panning (int track_id, <float panning>)
/live/return/panning (int track_id, <float panning>)
/live/master/panning (<float panning>)
    Sets / gets the mixer panning of track_id

/live/track/send (int track_id, int send_id, <float value>)
/live/return/send (int track_id, int send_id, <float value>)
/live/master/send (int send_id, <float value>)
    Sets / gets the mixer send_id of track_id


/live/track/select (int track_id)
/live/return/select (int track_id)
/live/master/select
    Selects the track

/live/track/crossfader (int track_id, <int state>)
/live/return/crossfader (int track_id, <int state>)
    Sets / gets the crossfader assignment of track_id (0=None, 1=A, 2=B)

/live/master/crossfader
    Sets / gets the master crossfader position


/live/track/name (int track_id, <string name>)
/live/return/name (int track_id, <string name>)
    Sets / gets the name of track_id

/live/track/color (int track_id, <int color>)
/live/return/color (int track_id, <int color>)
    Sets / gets the color of track_id


/live/track/stop (int track_id, <int state>)
/live/track/state (int track_id, <int state>)

/live/track/create (<int offset>)
/live/return/create (<int offset>)

/live/track/duplicate (int track_name) 
    Availble in API but not implemented
    
/live/track/input (string track_name or int track_id, string track_name or int track_id) 
/live/track/insub (string track_name or int track_id, int sublist_id or str sublist_name)

/live/track/output (string track_name or int track_id, string track_name or int track_id) 
/live/track/outsub (string track_name or int track_id, int sublist_id or str sublist_name)) 

/live/track/collapse (string track_name or int track_id)

Devices
-------

/live/track/devices (string track_name or int track_id, <int device_id>)
/live/return/devices (int track_id, <int device_id>)
/live/master/devices (<int device_id>)

/live/track/device/range
/live/return/device/range
/live/master/device/range


/live/track/device/param
/live/return/device/param
/live/master/device/param


/live/track/device/select
/live/return/device/select
/live/master/device/select




Clips
-----

/live/clip/state (int track_id, int scene_id)

/live/clip/play (int track_id, int scene_id)

/live/clip/stop (int track_id, int scene_id)

/live/clip/view (int track_id, int scene_id)

/live/clip/name (int track_id, int scene_id)

/live/clip/name/block (int track_id, int scene_id, int width, int height)

/live/clip/color (int track_id, int scene_id)


/live/clip/looping (int track_id, int scene_id)
/live/clip/loopstart (int track_id, int scene_id)
/live/clip/loopend (int track_id, int scene_id)
/live/clip/loopjump (int track_id, int scene_id)
/live/clip/start (int track_id, int scene_id)
/live/clip/end (int track_id, int scene_id)
/live/clip/warping (int track_id, int scene_id)
/live/clip/pitch (int track_id, int scene_id)


/live/clip/create (int track_id, int scene_id)
/live/clip/delete (int track_id, int scene_id)

warping mode
gain




Browser
-------

