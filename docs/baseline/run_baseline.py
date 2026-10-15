"""Run original BLT locally; writes evidence only, no installs or remote calls."""
import argparse, importlib.metadata, json, os, pathlib, platform, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = [
("en_count", "syllable-counter/count_syllables", ["Let it go", "en-us"], "Syllables: 3"),
("en_count_word", "syllable-counter/count_syllables", ["beautiful", "en-us"], "Syllables: 3"),
("zh_count", "syllable-counter/count_syllables", ["随它吧", "cmn"], "Syllables: 3"),
("zh_punctuation_digits", "syllable-counter/count_syllables", ["春風，吹過！123", "zh"], "Syllables: 4"),
("zh_mixed", "syllable-counter/count_syllables", ["春風 hello", "cmn"], "Syllables: 4"),
("en_rhyme_yes", "rhyme-analyzer/rhyme_analysis", ["cat", "en-us", "hat"], "Rhymes: True"),
("en_rhyme_no", "rhyme-analyzer/rhyme_analysis", ["cat", "en-us", "dog"], "Rhymes: False"),
("zh_rhyme_yes", "rhyme-analyzer/rhyme_analysis", ["春風", "cmn", "清風"], "Rhymes: True"),
("zh_rhyme_no", "rhyme-analyzer/rhyme_analysis", ["春風", "cmn", "花開"], "Rhymes: False"),
("zh_rhyme_punctuation", "rhyme-analyzer/rhyme_analysis", ["春風！", "cmn", "清風"], "Rhymes: True"),
("zh_scheme", "rhyme-analyzer/rhyme_analysis", ["--scheme", "cmn", "春風", "清風", "花開", "歸來"], "Rhyme scheme: AABB"),
("validator_pass", "lyrics-validator/validate", ["cmn", "[2,2]", "春風", "清風", "--rhyme", "AA"], {"syllables_match": True, "rhymes_valid": True}),
("validator_reject", "lyrics-validator/validate", ["cmn", "[3,2]", "春風", "花開", "--rhyme", "AA"], {"syllables_match": False, "rhymes_valid": False}),
("validator_distinct", "lyrics-validator/validate", ["cmn", "[2,2]", "春風", "清風", "--rhyme", "AB"], {"rhymes_valid": False}),
("validator_patterns", "lyrics-validator/validate", ["cmn", "[2,2]", "春風", "天空", "--patterns", "[[2],[2]]"], {"patterns_match": True}),
("validator_digits", "lyrics-validator/validate", ["cmn", "[2]", "春風123"], None),
("en_patterns", "syllable-pattern-analyzer/pattern_analysis", ["en-us", "Let it go"], "[1, 1, 1]"),
("zh_patterns", "syllable-pattern-analyzer/pattern_analysis", ["cmn", "春風吹過"], None),
("en_ipa", "phonetic-analyzer/phonetic_analysis", ["cat", "en-us", "hat"], None),
("zh_ipa", "phonetic-analyzer/phonetic_analysis", ["春風", "cmn", "天空"], None),
("ja_mora", "syllable-counter/count_syllables", ["さくら", "ja"], "Syllables: 3"),
]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", default=str(ROOT/"docs/baseline/results.json")); args=ap.parse_args()
    env=os.environ.copy(); env["PYTHONPATH"]=str(ROOT/"src"); env["PYTHONDONTWRITEBYTECODE"]="1"
    records=[]
    for name,skill,inputs,expected in CASES:
        directory,script=skill.split("/"); cmd=[sys.executable,str(ROOT/"skills"/directory/"scripts"/(script+".py")),*inputs]
        try:
            p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=60)
            match=None
            if expected is not None and p.returncode==0:
                match=all(json.loads(p.stdout).get(k)==v for k,v in expected.items()) if isinstance(expected,dict) else expected in p.stdout
            status="runtime_failure" if p.returncode else ("expectation_failure" if match is False else "pass" if match is True else "observation")
            record=dict(case=name,command=cmd,input=inputs,expected=expected,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,status=status)
        except subprocess.TimeoutExpired:
            record=dict(case=name,command=cmd,input=inputs,status="timeout")
        records.append(record); print(name,record["status"],flush=True)
    versions={d.metadata["Name"]:d.version for d in importlib.metadata.distributions()}
    output=dict(python=sys.version,executable=sys.executable,prefix=sys.prefix,platform=platform.platform(),head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),packages=versions,results=records)
    pathlib.Path(args.out).write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__": main()
