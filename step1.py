description = """
Step 1:
- Get information of songs: key, bpm, duration, structure_song
- Matching key, bpm between 2 songs
- Using LLM to recommend new structure_song for mashup song
"""
from copy import deepcopy
import json
from openai import OpenAI
import allin1

from configs.env import settings

from utils.bpm import change_bpm_with_pitch_lock
from utils.key import change_pitch

from madmom.features.key import CNNKeyRecognitionProcessor, key_prediction_to_label

key_recognizer = CNNKeyRecognitionProcessor()


def label_elements(data):
    # Handler verse-verse2-...
    counters = {}
    previous_label = None
    new_data = deepcopy(data)

    for index, item in enumerate(data):
        label = item["label"]
        if label != previous_label:
            counters[label] = 1
            count = 1
        else:
            counters[label] += 1
            count = counters[label]

        new_label = f"{label} {count}" if counters[label] > 1 else label
        new_data[index]["label"] = new_label
        previous_label = label

    return new_data


def handler_start_end_songs(master_song_seg: list, slave_song_seg: list):
    # master
    while "start" in master_song_seg[0]['label']:
        if master_song_seg[1]["label"] == "intro":
            master_song_seg[1]["start"] = 0.0
        master_song_seg.pop(0)
    while "end" in master_song_seg[-1]['label']:
        if master_song_seg[-2]["label"] == "outro":
            master_song_seg[-2]["end"] = master_song_seg[-1]["end"]
        master_song_seg.pop(-1)
    master_song_seg = [seg for seg in master_song_seg if "start" not in seg["label"]
                       and "end" not in seg["label"]]

    # slave
    while "end" in slave_song_seg[-1]['label']:
        if slave_song_seg[-2]["label"] == "outro":
            slave_song_seg[-2]["end"] = slave_song_seg[-1]["end"]
        slave_song_seg.pop(-1)
    slave_song_seg = [seg for seg in slave_song_seg if "start" not in seg["label"]
                      and "intro" not in seg["label"]
                      and "end" not in seg["label"]]

    return master_song_seg, slave_song_seg


# Music Structure Analyzer
def analyzer_song(songs: list):
    result = allin1.analyze(
        songs,
        device="cuda"
    )

    outputs = []
    for res in result:
        # song = KeyFinder(res.path.as_posix())
        key = key_prediction_to_label(key_recognizer(res.path.as_posix()))

        info = {}
        info["filename"] = res.path.as_posix()
        info["key"] = key
        info["bpm"] = res.bpm
        info["time_signature"] = str(max(res.beat_positions)) + "/4"
        info["duration"] = res.segments[-1].end
        info["downbeats"] = res.downbeats
        info["segments"] = [e.__dict__ for e in res.segments]
        info["segments"] = label_elements(info["segments"])

        outputs.append(info)

    index_map = {filename: index for index, filename in enumerate(songs)}
    sorted_output = sorted(outputs, key=lambda x: index_map[x['filename']])

    # Remove start-end label
    sorted_output[0]['segments'], sorted_output[1]['segments'] = handler_start_end_songs(sorted_output[0]['segments'],
                                                                                         sorted_output[1]['segments'])

    for res in sorted_output:
        res["structure_song"] = [item["label"] for item in res["segments"]]

    return sorted_output


def beat_matching(songs: list, match_key: bool, match_bpm: bool):
    """
    Match key/bpm song_2 with song_1
    songs: [
        {'filename': 'a.mp3", 'key': 'D# major', 'bpm': 105},
        {'filename': 'b.mp3', 'key': 'A minor', 'bpm': 70,}
     ]
    """
    # Change key, bpm of song 2
    songs_matched = deepcopy(songs)
    audio_path2_mix = songs_matched[1]['filename']
    if match_key:
        audio_path2_mix = change_pitch(audio_path2_mix, songs_matched[1]['key'], songs_matched[0]['key'])
    if match_bpm:
        audio_path2_mix = change_bpm_with_pitch_lock(audio_path2_mix, songs[1]['bpm'], songs[0]['bpm'])
    # Get new information of song 2: key, bpm, duration, structure_song
    if audio_path2_mix != songs_matched[1]['filename']:
        songs_matched[1] = analyzer_song([audio_path2_mix])[0]
    return songs_matched


def gen_mashup_structure(songs: list):
    """Using OpenAI gen structure song of mashup

    [{
        "filename": "a.mp3",
        "keys": {"key_primary": "G minor", "key_alt": "D# major"},
        "bpm": 105, "time_signature": "4/4",
        "duration": 234.02,
        "segments": [{"start": 0.35, "end": 23.17, "label": "intro"}, ...],
        "structure_song": ["intro", "verse", "verse", "chorus", "verse", "verse", "chorus", ...]
    },
    ...
    ]

    """

    # System prompt
    system_prompt = f"""You are a GPT, a large language model created by PlayGround."""
    system_prompt += """
You are an AI assistant specialized in music composition and arrangement. Your role is to create a new song structure for a mashup song.
When given two song structures, you will:
1. With each song, identify and keep original each song's harmonic pairs (e.g. 'verse-chorus', 'bridge-chorus', ...).
Commonly used harmonic pairs in a song: [
    'intro-verse', 'verse-chorus', 'chorus-verse', 
    'verse-bridge', 'bridge-chorus',
    'chorus-solo', 'solo-chorus',
    'chorus-inst', 'inst-chorus',
    'break-chorus', 'break-outro', 
    'verse-outro', 'chorus-outro',
]
2. Create a new structure for the song mashup, by combining single or adjacent harmonies, using all harmony types/labels to create new structures if any appear.
3. Ensure that transitions between labels are smooth and musically logical, Avoid switching single or double harmonies multiple times in a row.
4. Create a new name for the mashup song, using keywords from the 2 song names, then add new words to create a new meaningful and cool name.


Rules to follow when creating a new structure for a mashup song:
- Identical labels cannot be next to each other (e.g. 'intro-intro', 'verse-verse', 'chorus-chorus'), they must follow the sequential rule ('verse-verse 2-verse 3', 'chorus-chorus 2-chorus 3' .etc).
- In the new structure mashup song, labels with the same song_position should not stand next to each other too much, maximum 1-2 labels.

You output is json format includes:
- filename_mashup_song (str): New name of the mashup song.
- structure_mashup_song (list): New structure of mashup song, each elements must have:
    + song_position (int): position of song, (include Song 0 / Song 1)
    + label (str): is song labels (e.g., verse, chorus, bridge, ...).
    + position (int): position of label in song labels.

Example input format:
- Song 0: {"filename": "Wake_Me_Up.mp3", "structure_song": ["intro", "verse", "verse 2", "chorus", "verse", "verse 2", "chorus", "chorus 2", "bridge", "chorus", "chorus 2", "chorus 3"], "length_structure": 12}
- Song 1: {"filename": "Never_Gonna_Give_You_Up.mp3", "structure_song": ["intro", "intro 2", "verse", "verse 2", "chorus", "verse", "chorus", "chorus 2", "chorus 3", "chorus 4"], "length_structure": 10}

Example for format GPT json outputs:
{
    "filename_mashup_song": "Never Wake To Give Me Up"
    "structure_mashup_song": [{"song_position": 0, "label": "intro", "position": 0}, {"song_position": 0, "label": "verse", "position": 1}, {"song_position": 1, "label": "verse 2", "position": 3}, {"song_position": 1, "label": "chorus", "position": 4}, {"song_position": 0, "label": "chorus 2", "position": 8}, ...],
}
"""

    song_0 = {
        "filename": songs[0]['filename'],
        "structure": songs[0]['structure_song'],
        "length_structure": len(songs[0]['structure_song'])
    }
    song_1 = {
        "filename": songs[1]['filename'],
        "structure": songs[1]['structure_song'],
        "length_structure": len(songs[1]['structure_song'])
    }

    # User prompt
    user_prompt = f"""Create a new mashup song from input is:
- Song 0: {str(song_0)}
- Song 1: {str(song_1)}
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Log message
    mess_str = ""
    for mess in messages:
        mess_str += "\n" + json.dumps(mess, ensure_ascii=False)

    # Model
    client = OpenAI(api_key=settings.OPENAI_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=messages
    )
    output = json.loads(response.choices[0].message.content, strict=False)

    input_str = ""
    for mess in messages:
        input_str += f"{mess['content']}\n"
    input_str = input_str.strip()

    metadata = {
        "task": "generate_prompt",
        "model": "gpt-4o",
        "usage": {
            "openAI": {"unit": "tokens/$",
                       "input": num_tokens_from_string_openai(input_str, "gpt-4o"),
                       "output": num_tokens_from_string_openai(response.choices[0].message.content, "gpt-4o"),
                       "price": "https://openai.com/api/pricing/"
                       }
        }
    }

    return output, metadata


def num_tokens_from_string_openai(string: str, model_name: str) -> int:
    import tiktoken

    # if model_name == "gpt-4o":
    #     encoding_name = "o200k_base"
    # else:
    #     encoding_name = "cl100k_base"

    encoding_name = "cl100k_base"
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


if __name__ == "__main__":
    audio_path1 = "/media/data/liem/music_mashup/test/Orange.mp3"
    audio_path2 = "/media/data/liem/music_mashup/test/Tháng Tư Là Lời Nói Dối Của Em.mp3"

    songs = analyzer_song([audio_path1, audio_path2])
    print("Song analyzed: ")
    print(songs)

    songs = beat_matching(songs, False, False)
    print("Song analyzed when matched: ")
    print(songs)

    struct_mashup_song, metadata = gen_mashup_structure(songs)
    print("Generate new structure of mashup song: ")

    print(struct_mashup_song)
    print(metadata)
