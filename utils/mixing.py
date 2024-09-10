import os
import time
import pydub
import numpy

from utils.pycrossfade.song import Song
from utils.pycrossfade.transition import crossfade
from utils.pycrossfade.utils import save_audio


def mixing_section(master_song, slave_song, large_master: bool = True):
    os.makedirs("pycrossfade_annotations", exist_ok=True)
    song_1 = os.path.join("pycrossfade_annotations", f"0_{int(time.time()*10**5)}.mp3")
    song_2 = os.path.join("pycrossfade_annotations", f"1_{int(time.time()*10**5)}.mp3")

    if isinstance(master_song, pydub.audio_segment.AudioSegment):
        master_song.export(song_1, format='mp3')
    elif isinstance(master_song, numpy.ndarray):
        save_audio(master_song, song_1)
    slave_song.export(song_2, format='mp3')
    try:
        output_np = crossfade(Song(song_1), Song(song_2), len_crossfade=2, len_time_stretch=2, large_master=large_master)
    # except TypeError:
    #     raise ValueError("The song is too short, please mix it with a longer part")
    # except IndexError:
    #     raise ValueError("The song is too short, please mix it with a longer part")
    except Exception as e:
        print("[Warning]: Can't combine this section. Skipping...")
        return master_song
    try:
        os.remove(song_1)
        os.remove(song_1.replace(".mp3", ".txt"))
        os.remove(song_2)
        os.remove(song_2.replace(".mp3", ".txt"))
    except:
        pass

    return output_np
