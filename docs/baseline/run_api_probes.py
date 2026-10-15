"""Original API probes; synthetic inputs, no generation or service calls."""
import contextlib, io, json, pathlib, sys, traceback
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src")); sys.path.insert(0,str(ROOT/"scripts"))
from blt_skills import analyze_pattern_alignment, score_syllable_patterns, verify_all_constraints, detect_rhyme_scheme, calculate_ipa_similarity
from blt_skills.phonetics import _phonemize_via_backend
from blt_skills.ccvo import ccvo_distance
from bench_common import evaluate_song
CASES=[
("pattern_exact", lambda: analyze_pattern_alignment([1,2],[1,2])),
("pattern_mismatch", lambda: analyze_pattern_alignment([1,2],[2,1])),
("pattern_score", lambda: score_syllable_patterns([[1,2]],[[1,2]])),
("ipa_identity", lambda: calculate_ipa_similarity("kæt","kæt")),
("strict_espeak_en", lambda: _phonemize_via_backend("cat","en-us")),
("strict_espeak_zh", lambda: _phonemize_via_backend("春風","cmn")),
("validator_length_mismatch", lambda: verify_all_constraints(["春風"],"cmn",[2,2])),
("validator_pattern_mismatch", lambda: verify_all_constraints(["春風"],"cmn",[2],target_patterns=[[1,1]])),
("empty_scheme", lambda: detect_rhyme_scheme([],"cmn")),
("ccvo_identity", lambda: ccvo_distance(["cat"],["cat"],"en-us","en-us")),
("ccvo_en_zh", lambda: ccvo_distance(["cat"],["貓"],"en-us","cmn")),
("synthetic_metrics", lambda: evaluate_song({"id":"synthetic_001","metadata":{"artist":"HW2 synthetic fixture"},"source_lines":["cat","hat"],"source_lang":"en-us","target_lang":"cmn"},["風","東"]))
]
def main():
    results=[]
    for name,fn in CASES:
        err=io.StringIO()
        try:
            with contextlib.redirect_stderr(err): output=fn()
            result=dict(case=name,output=output,stderr=err.getvalue(),status="executed")
        except Exception:
            result=dict(case=name,status="runtime_failure",stderr=err.getvalue()+traceback.format_exc())
        results.append(result); print(json.dumps(result,ensure_ascii=False),flush=True)
    (ROOT/"docs/baseline/api-results.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__": main()
