"""Offline credential checks; all credentials below are synthetic fixtures."""
import os,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
from hw2_translation.credential_check import validate_key

class CredentialTests(unittest.TestCase):
 def test_missing_quotes_whitespace_rejected(self):
  for value in ['', ' synthetic', 'synthetic\n', 'syn thetic', '"synthetic"', "'synthetic'"]:
   with self.subTest(kind=repr(value)):
    with self.assertRaises(ValueError):validate_key(value)
 def test_safe_result_has_no_secret_or_fingerprint(self):
  result=validate_key('synthetic-credential-fixture')
  self.assertEqual(result,{'key_received_by_python':True,'input_checks_passed':True,'validity_verified_with_google':False})
 def test_actual_shell_handoff_block_exports_key_to_python(self):
  # Execute the exact read/export block from the startup script with a synthetic input.
  source=Path('scripts/start_csd_phase4b.sh').read_text()
  block=source[source.index('unset HW2_LLM_API_KEY'):source.index('.venv-ui/bin/python -m hw2_translation.credential_check')]
  block=block.replace('</dev/tty','').replace('>/dev/tty','>/dev/null')
  check="import os; assert os.environ.get('HW2_LLM_API_KEY')=='synthetic-credential-fixture'; print('handoff_verified')"
  import shlex
  cmd='set +x\nset -euo pipefail\n'+block+'\n'+shlex.quote(sys.executable)+' -c '+shlex.quote(check)
  env={k:v for k,v in os.environ.items() if not k.startswith(('HW2_LLM_','GEMINI_','GOOGLE_API'))}
  run=subprocess.run(['bash','-c',cmd],input='synthetic-credential-fixture\n',text=True,capture_output=True,env=env)
  self.assertEqual(run.returncode,0);self.assertIn('handoff_verified',run.stdout)
  self.assertNotIn('synthetic-credential-fixture',run.stdout+run.stderr)

if __name__=='__main__':unittest.main()
