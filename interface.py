import re
import subprocess
import json


def mashup_music(mode, master, slave, match_key: bool = False, match_bpm: bool = False):
    """
    model: ['auto', 'manual']
    """
    args = ["python", "main.py", mode, master, slave]
    if match_key:
        args.append("--match_key")
    if match_bpm:
        args.append("--match_bpm")

    print(args)
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=True,
    )
    print(result.stdout)
    # print(result.stderr)

    output = result.stdout.strip()
    json_match = re.search(r'(\{.*\})', output.split('\n')[-1])
    if json_match:
        json_output = json_match.group(0)
        print(json_output)
        output = json.loads(json_output, strict=False)
    else:
        raise Exception("No JSON output found")

    if "error" in output:
        if output['error']['type'] == "ValueError":
            raise ValueError(output['error']['message'])
        elif output['error']['type'] == "Exception":
            raise Exception(output['error']['message'])

    return output['filename'], output['metadata'], output['song_structure'], output['execution_time']
