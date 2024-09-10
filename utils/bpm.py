import os
import librosa
import soundfile as sf


def change_bpm_with_pitch_lock(audio_path, original_bpm, new_bpm, match_half_bpm: bool = True):
    if original_bpm == new_bpm:
        return audio_path

    if match_half_bpm:
        new_bpm = original_bpm + int((new_bpm - original_bpm) / 2)

    file_name, fmt = os.path.splitext(os.path.basename(audio_path))[0], os.path.splitext(os.path.basename(audio_path))[1]
    output_path = os.path.join(os.path.dirname(audio_path), f"{file_name}_{new_bpm}bpm{fmt}")

    y, sr = librosa.load(audio_path, sr=None)
    rate = new_bpm / original_bpm
    y_stretched = librosa.effects.time_stretch(y=y, rate=rate)
    sf.write(output_path, y_stretched, sr)

    return output_path


# audio_path = "/media/data/liem/music_mashup/music/4.4/Y2meta.app - Adele - Rolling in the Deep (Official Music Video) (128 kbps).mp3"
# change_bpm_with_pitch_lock(audio_path, 105, 20)
