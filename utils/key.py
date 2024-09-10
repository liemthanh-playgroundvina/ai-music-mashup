import os

import librosa
import soundfile as sf


def semitones_between(original_tone, target_tone):
    notes = ['C major', 'Db major', 'D major', 'Eb major', 'E major', 'F major', 'Gb major', 'G major', 'Ab major', 'A major', 'Bb major', 'B major']
    minor_to_major = {
        'A minor': 'C major',
        'A# minor': 'Db major',
        'Bb minor': 'Db major',
        'B minor': 'D major',
        'C minor': 'Eb major',
        'C# minor': 'E major',
        'Db minor': 'E major',
        'D minor': 'F major',
        'D# minor': 'Gb major',
        'Eb minor': 'Gb major',
        'E minor': 'G major',
        'F minor': 'Ab major',
        'F# minor': 'A major',
        'Gb minor': 'A major',
        'G minor': 'Bb major',
        'G# minor': 'B major',
        'Ab minor': 'B major',
    }
    original_tone = minor_to_major.get(original_tone, original_tone)
    target_tone = minor_to_major.get(target_tone, target_tone)

    original_index = notes.index(original_tone)
    target_index = notes.index(target_tone)

    semitones = target_index - original_index
    if semitones > 6:
        semitones -= 12
    elif semitones < -5:
        semitones += 12
    # print(original_tone, target_tone)
    # print(original_index, target_index)
    # print(semitones)
    return semitones


def change_pitch(audio_path, ori_tone, tar_tone):
    semitone_change = semitones_between(ori_tone, tar_tone)
    if semitone_change == 0:
        return audio_path

    file_name, fmt = os.path.splitext(os.path.basename(audio_path))[0], os.path.splitext(os.path.basename(audio_path))[1]
    if semitone_change > 0:
        output_path = os.path.join(os.path.dirname(audio_path), f"{file_name}_+{semitone_change}{fmt}")
    else:
        output_path = os.path.join(os.path.dirname(audio_path), f"{file_name}_{semitone_change}{fmt}")

    y, sr = librosa.load(path=audio_path, sr=None)
    y_shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=semitone_change)
    sf.write(output_path, y_shifted, sr)

    return output_path
