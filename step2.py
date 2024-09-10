import os

description = """
Step 2:
- Split songs, and concat into new mashup song.
"""

from pydub import AudioSegment
from utils.mixing import mixing_section
from utils.pycrossfade.utils import save_audio


class AudioEditor:
    def __init__(self, master, slave, mashup):
        """
        master: {'filename': n.mp3', 'key': 'F major', 'bpm': 107, 'time_signature': '4/4', 'duration': 163.66, 'segments': [{'start': 0.0, 'end': 0.42, 'label': 'start'}, {'start': 0.42, 'end': 27.02, 'label': 'verse'}, {'start': 27.02, 'end': 44.25, 'label': 'verse'}, {'start': 44.25, 'end': 60.37, 'label': 'verse'}, {'start': 60.37, 'end': 78.14, 'label': 'chorus'}, {'start': 78.14, 'end': 95.36, 'label': 'verse'}, {'start': 95.36, 'end': 111.49, 'label': 'verse'}, {'start': 111.49, 'end': 129.26, 'label': 'chorus'}, {'start': 129.26, 'end': 147.03, 'label': 'chorus'}, {'start': 147.03, 'end': 163.63, 'label': 'bridge'}, {'start': 163.63, 'end': 163.66, 'label': 'chorus'}], 'structure_song': ['start', 'verse', 'verse', 'verse', 'chorus', 'verse', 'verse', 'chorus', 'chorus', 'bridge', 'chorus']},
        slave: {'filename': 'm.mp3', 'key': 'D minor', 'bpm': 107, 'time_signature': '4/4', 'duration': 214.33, 'segments': [{'start': 0.0, 'end': 1.01, 'label': 'start'}, {'start': 1.01, 'end': 18.39, 'label': 'intro'}, {'start': 18.39, 'end': 45.85, 'label': 'verse'}, {'start': 45.85, 'end': 73.59, 'label': 'chorus'}, {'start': 73.59, 'end': 100.5, 'label': 'verse'}, {'start': 100.5, 'end': 129.66, 'label': 'chorus'}, {'start': 129.66, 'end': 146.48, 'label': 'verse'}, {'start': 146.48, 'end': 163.29, 'label': 'chorus'}, {'start': 163.29, 'end': 183.49, 'label': 'chorus'}, {'start': 183.49, 'end': 210.86, 'label': 'outro'}, {'start': 210.86, 'end': 214.33, 'label': 'end'}], 'structure_song': ['start', 'intro', 'verse', 'chorus', 'verse', 'chorus', 'verse', 'chorus', 'chorus', 'outro', 'end']}
        mashup: [{"filename": 'a.mp3', "start": 0, "end": 1.1, "label": "verse"}, ...]
        """
        self.audio_segments = None
        self.master = master
        self.slave = slave
        self.mashup = mashup

    def create(self):
        for i, v in enumerate(self.mashup):
            if i == 0 or i == len(self.mashup) - 1:
                start, end, large_master = self.get_time_mashup(v['filename'], v['start'], v['end'], ["", v['label'], ""], True)
                self.edit_audio(v['filename'], start, end, large_master)
            else:
                start, end, large_master = self.get_time_mashup(
                    v['filename'], v['start'], v['end'],
                    [self.mashup[i - 1]['label'], v['label'], self.mashup[i + 1]['label']]
                )
                self.edit_audio(v['filename'], start, end, large_master)

    def get_time_mashup(self, filename, start_time, end_time, sections: list, handler_boundary=False):
        """Set rule to get time following sections
        sections (list): include [section - 1, curr_section, section + 1] position in mashup
        """
        song = [item for item in [self.master, self.slave] if item.get('filename') == filename][0]
        idx_start, _ = self.find_downbeats_position(start_time, song['downbeats'])
        idx_end, _ = self.find_downbeats_position(end_time, song['downbeats'])

        # Handler [first,end] sections
        if handler_boundary:
            if idx_start <= 1:
                new_idx_start = 0
                value_start = 0
            else:
                new_idx_start = idx_start
                value_start = song['downbeats'][idx_start]
            if idx_end >= len(song['downbeats']) - 2:
                new_idx_end = len(song['downbeats'])
                value_end = song['duration']
            else:
                new_idx_end = idx_end
                value_end = song['downbeats'][idx_end]

            print(f"Label: {sections[1]}, Start|End: Downbeat {new_idx_start-idx_start}|{new_idx_end-idx_end}, Large Master: {True}")
            return value_start, value_end, True

        # Handler following position of section
        new_idx_start = idx_start - 2
        if "chorus" in sections[-1]:
            new_idx_end = idx_end + 1
        else:
            new_idx_end = idx_end

        if new_idx_start < 0:
            new_idx_start = 0
        if new_idx_end > len(song['downbeats']) - 1:
            new_idx_end = len(song['downbeats']) - 1

        # Handler mashup volume
        if "chorus" in sections[0]:
            large_master = False
        else:
            large_master = True

        print(f"Label: {sections[1]}, Start|End: Downbeat {new_idx_start-idx_start}|{new_idx_end-idx_end}, Large Master: {large_master}")
        return song['downbeats'][new_idx_start], song['downbeats'][new_idx_end], large_master

    @staticmethod
    def find_downbeats_position(time: float, downbeats: list):
        value_time = min(downbeats, key=lambda x: abs(x - time))
        index_time = downbeats.index(value_time)
        return index_time, value_time

    def edit_audio(self, input_file: str, start_time: float, end_time: float, large_master: bool = True):
        audio = AudioSegment.from_mp3(input_file)
        start_time_ms, end_time_ms = int(start_time * 1000), int(end_time * 1000)
        if end_time_ms - start_time_ms > 2000:
            if self.audio_segments is None:
                self.audio_segments = audio[start_time_ms:end_time_ms]
            else:
                self.audio_segments = mixing_section(self.audio_segments, audio[start_time_ms:end_time_ms], large_master)

    def export_audio(self, output_file: str):
        save_audio(self.audio_segments, output_file)
        print(f"Mashup song exported to {output_file}")


def mashup(songs_analyzed: list, structure_mashup: dict):
    """
    -    songs_analyzed: [
        {'filename': '/media/data/liem/music_mashup/music/4.4/Set Fire to the Rain.mp3', 'key': 'F major', 'bpm': 107, 'time_signature': '4/4', 'duration': 163.66, 'segments': [{'start': 0.0, 'end': 0.42, 'label': 'start'}, {'start': 0.42, 'end': 27.02, 'label': 'verse'}, {'start': 27.02, 'end': 44.25, 'label': 'verse'}, {'start': 44.25, 'end': 60.37, 'label': 'verse'}, {'start': 60.37, 'end': 78.14, 'label': 'chorus'}, {'start': 78.14, 'end': 95.36, 'label': 'verse'}, {'start': 95.36, 'end': 111.49, 'label': 'verse'}, {'start': 111.49, 'end': 129.26, 'label': 'chorus'}, {'start': 129.26, 'end': 147.03, 'label': 'chorus'}, {'start': 147.03, 'end': 163.63, 'label': 'bridge'}, {'start': 163.63, 'end': 163.66, 'label': 'chorus'}], 'structure_song': ['start', 'verse', 'verse', 'verse', 'chorus', 'verse', 'verse', 'chorus', 'chorus', 'bridge', 'chorus']},
        {'filename': '/media/data/liem/music_mashup/music/4.4/In The End_-1_107bpm.mp3', 'key': 'D minor', 'bpm': 107, 'time_signature': '4/4', 'duration': 214.33, 'segments': [{'start': 0.0, 'end': 1.01, 'label': 'start'}, {'start': 1.01, 'end': 18.39, 'label': 'intro'}, {'start': 18.39, 'end': 45.85, 'label': 'verse'}, {'start': 45.85, 'end': 73.59, 'label': 'chorus'}, {'start': 73.59, 'end': 100.5, 'label': 'verse'}, {'start': 100.5, 'end': 129.66, 'label': 'chorus'}, {'start': 129.66, 'end': 146.48, 'label': 'verse'}, {'start': 146.48, 'end': 163.29, 'label': 'chorus'}, {'start': 163.29, 'end': 183.49, 'label': 'chorus'}, {'start': 183.49, 'end': 210.86, 'label': 'outro'}, {'start': 210.86, 'end': 214.33, 'label': 'end'}], 'structure_song': ['start', 'intro', 'verse', 'chorus', 'verse', 'chorus', 'verse', 'chorus', 'chorus', 'outro', 'end']}
        ]

    -    structure_mashup: {'filename_mashup_song': 'Set Fire In The End', 'structure_mashup_song': [
        {'song_position': 0, 'label': 'start', 'position': 0},
        ...
        ]}

    """
    # Make list sections of mashup song from master/slave
    new_song = []
    for struct in structure_mashup['structure_mashup_song']:
        song_position = struct['song_position']
        section_position = struct['position']
        new_song.append({
            "filename": songs_analyzed[song_position]['filename'],
            "start": songs_analyzed[song_position]['segments'][section_position]['start'],
            "end": songs_analyzed[song_position]['segments'][section_position]['end'],
            "label": struct['label']
        })

    new_song_merged = []
    for segment in new_song:
        if new_song_merged and segment['filename'] == new_song_merged[-1]['filename']:
            new_song_merged[-1]['end'] = max(new_song_merged[-1]['end'], segment['end'])
        else:
            new_song_merged.append(segment)

    print("--- Structure Mashup Song ---")
    print(new_song_merged)
    print("--- End Structure Mashup Song ---")

    editor = AudioEditor(songs_analyzed[0], songs_analyzed[1], new_song_merged)
    editor.create()

    filename_mashup = f"{structure_mashup['filename_mashup_song']} (Mashup).mp3"
    path_mashup = os.path.join(os.path.dirname(songs_analyzed[0]['filename']), filename_mashup)
    editor.export_audio(path_mashup)

    return path_mashup, new_song_merged


if __name__ == "__main__":
    songs = [{'filename': '/media/data/liem/music_mashup/test/Orange.mp3', 'key': 'G major', 'bpm': 86, 'time_signature': '4/4', 'duration': 163.66, 'downbeats': [1.37, 4.44, 7.21, 10.0, 12.8, 15.59, 18.39, 21.18, 23.96, 26.75, 29.54, 32.33, 35.12, 37.91, 40.71, 43.49, 46.3, 49.07, 51.87, 54.66, 57.45, 60.24, 63.04, 65.82, 68.62, 71.39, 74.19, 76.98, 79.76, 82.56, 85.36, 88.15, 90.93, 93.72, 96.53, 99.32, 102.11, 104.9, 107.69, 110.47, 113.27, 116.06, 118.85, 121.64, 124.43, 127.22, 130.01, 132.8, 135.59, 138.38, 141.17, 143.97, 146.76, 149.54, 152.34, 155.13, 157.92, 160.71, 163.51], 'segments': [{'start': 0.0, 'end': 1.36, 'label': 'start'}, {'start': 1.36, 'end': 23.96, 'label': 'intro'}, {'start': 23.96, 'end': 51.87, 'label': 'verse'}, {'start': 51.87, 'end': 68.62, 'label': 'verse 2'}, {'start': 68.62, 'end': 93.72, 'label': 'verse 3'}, {'start': 93.72, 'end': 118.85, 'label': 'chorus'}, {'start': 118.85, 'end': 143.96, 'label': 'chorus 2'}, {'start': 143.96, 'end': 163.49, 'label': 'verse'}, {'start': 163.49, 'end': 163.66, 'label': 'verse 2'}], 'structure_song': ['start', 'intro', 'verse', 'verse 2', 'verse 3', 'chorus', 'chorus 2', 'verse', 'verse 2']}, {'filename': '/media/data/liem/music_mashup/test/Tháng Tư Là Lời Nói Dối Của Em.mp3', 'key': 'C major', 'bpm': 67, 'time_signature': '4/4', 'duration': 370.4, 'downbeats': [31.49, 35.02, 38.64, 42.23, 45.82, 49.38, 52.97, 56.56, 60.14, 63.71, 67.3, 70.88, 74.46, 78.05, 81.63, 85.21, 88.79, 92.39, 95.96, 99.55, 103.07, 106.7, 110.28, 113.86, 117.46, 121.05, 124.62, 128.18, 131.78, 135.38, 138.96, 142.56, 146.06, 149.69, 153.29, 156.87, 160.45, 164.04, 167.62, 171.2, 174.78, 178.36, 181.95, 185.53, 189.11, 192.69, 196.28, 199.86, 203.44, 207.02, 210.61, 214.19, 217.77, 221.35, 224.93, 228.51, 232.1, 235.69, 239.28, 242.86, 246.56, 250.34, 254.06, 257.9, 261.92, 265.79, 269.67, 273.29, 276.82, 280.38, 283.96, 287.55, 291.13, 294.71, 298.29, 301.87, 305.43, 309.01, 312.59, 316.19, 319.78, 323.37, 326.95, 330.53], 'segments': [{'start': 0.0, 'end': 5.03, 'label': 'start'}, {'start': 5.03, 'end': 29.21, 'label': 'intro'}, {'start': 29.21, 'end': 49.38, 'label': 'intro 2'}, {'start': 49.38, 'end': 64.69, 'label': 'verse'}, {'start': 64.69, 'end': 91.48, 'label': 'verse 2'}, {'start': 91.48, 'end': 105.99, 'label': 'verse 3'}, {'start': 105.99, 'end': 120.14, 'label': 'chorus'}, {'start': 120.14, 'end': 136.68, 'label': 'chorus 2'}, {'start': 136.68, 'end': 153.28, 'label': 'inst'}, {'start': 153.28, 'end': 168.51, 'label': 'verse'}, {'start': 168.51, 'end': 181.94, 'label': 'verse 2'}, {'start': 181.94, 'end': 196.27, 'label': 'chorus'}, {'start': 196.27, 'end': 209.68, 'label': 'chorus 2'}, {'start': 209.68, 'end': 224.93, 'label': 'chorus 3'}, {'start': 224.93, 'end': 259.45, 'label': 'chorus 4'}, {'start': 259.45, 'end': 276.81, 'label': 'break'}, {'start': 276.81, 'end': 291.13, 'label': 'verse'}, {'start': 291.13, 'end': 305.42, 'label': 'chorus'}, {'start': 305.42, 'end': 319.78, 'label': 'chorus 2'}, {'start': 319.78, 'end': 332.31, 'label': 'chorus 3'}, {'start': 332.31, 'end': 355.27, 'label': 'outro'}, {'start': 355.27, 'end': 370.39, 'label': 'end'}, {'start': 370.39, 'end': 370.4, 'label': 'end 2'}], 'structure_song': ['start', 'intro', 'intro 2', 'verse', 'verse 2', 'verse 3', 'chorus', 'chorus 2', 'inst', 'verse', 'verse 2', 'chorus', 'chorus 2', 'chorus 3', 'chorus 4', 'break', 'verse', 'chorus', 'chorus 2', 'chorus 3', 'outro', 'end', 'end 2']}]

    mashup_song = {'filename_mashup_song': 'Orange Lời Nói Dối Tháng Tư', 'structure_mashup_song': [{'song_position': 0, 'label': 'start', 'position': 0}, {'song_position': 0, 'label': 'intro', 'position': 1}, {'song_position': 0, 'label': 'verse', 'position': 2}, {'song_position': 1, 'label': 'verse 2', 'position': 4}, {'song_position': 1, 'label': 'verse 3', 'position': 5}, {'song_position': 0, 'label': 'chorus', 'position': 5}, {'song_position': 0, 'label': 'chorus 2', 'position': 6}, {'song_position': 0, 'label': 'verse', 'position': 7}, {'song_position': 1, 'label': 'chorus', 'position': 11}, {'song_position': 1, 'label': 'chorus 2', 'position': 12}, {'song_position': 1, 'label': 'chorus 3', 'position': 13}, {'song_position': 1, 'label': 'outro', 'position': 20}, {'song_position': 1, 'label': 'end', 'position': 21}]}

    mashup_file = mashup(songs, mashup_song)
    print(mashup_file)
