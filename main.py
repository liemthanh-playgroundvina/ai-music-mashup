import argparse
import json
import time

from step1 import analyzer_song, beat_matching, gen_mashup_structure
from step2 import mashup
import logging

logging.basicConfig(level=logging.ERROR)
logging.getLogger('natten.functional').setLevel(logging.ERROR)
logging.getLogger('demucs').setLevel(logging.ERROR)
logging.getLogger('allin1').setLevel(logging.ERROR)


def ai_mashup_music(audio_path1, audio_path2, match_key: bool = False, match_bpm: bool = False):
    try:
        songs_structure = {}
        # Step 1
        print("*** Step 1.0 - Song analyzed: ")
        songs_analyzed = analyzer_song([audio_path1, audio_path2])
        songs_structure['original'] = songs_analyzed
        print(songs_analyzed)

        print("*** Step 1.1 - Song analyzed because matched: ")
        songs_matched = beat_matching(songs_analyzed, match_key, match_bpm)
        songs_structure['matched'] = songs_matched
        if songs_matched != songs_analyzed:
            print(songs_matched)

        print("*** Step 1.2 - Generate new structure of mashup song: ")
        struct_mashup_song, metadata_gpt = gen_mashup_structure(songs_matched)
        songs_structure['recommend'] = struct_mashup_song
        print(struct_mashup_song)

        # Step 2
        print("*** Step 2 - Mashup song file: ")
        mashup_file, mashup_structure = mashup(songs_matched, struct_mashup_song)
        songs_structure['mashup'] = mashup_structure
        print(mashup_file)

        return mashup_file, metadata_gpt, songs_structure

    except Exception as e:
        raise Exception(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', type=str, choices=['auto', 'manual'], help='mode mashup')
    parser.add_argument("master_audio", type=str, help="master_audio")
    parser.add_argument("slave_audio", type=str, help="slave_audio")
    parser.add_argument("--match_key", action='store_true', help="match_key")
    parser.add_argument("--match_bpm", action='store_true', help="match_bpm")
    args = parser.parse_args()

    result = {}
    start_time = time.time()

    try:
        if args.mode == 'auto':
            file_mashup, metadata, song_structure = ai_mashup_music(args.master_audio, args.slave_audio, args.match_key, args.match_bpm)
            result['filename'], result['metadata'], result['song_structure'] = file_mashup, metadata, song_structure

    except ValueError as e:
        result["error"] = {"type": "ValueError", "message": str(e)}
    except Exception as e:
        if str(e) == "The song is too short, please mix it with a longer part":
            result["error"] = {"type": "ValueError", "message": str(e)}
        else:
            result["error"] = {"type": "Exception", "message": str(e)}
    finally:
        result["execution_time"] = time.time() - start_time

    print(json.dumps(result, ensure_ascii=False))

