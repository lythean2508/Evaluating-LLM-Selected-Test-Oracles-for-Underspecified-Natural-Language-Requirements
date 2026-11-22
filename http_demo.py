"""Launch the prepared HTTP demo from the replication directory."""
from pathlib import Path
import runpy
import sys


ROOT=Path(__file__).resolve().parent
demo=ROOT.parent/'HTTP-Demo'/'Chay-HTTP-Demo.py'
if not demo.is_file():
    sys.exit('Khong tim thay HTTP-Demo/Chay-HTTP-Demo.py canh thu muc replication-v1.0.0. '
             'Giu hai thu muc nay trong cung thu muc Research.')
sys.argv[0]=str(demo)
runpy.run_path(str(demo),run_name='__main__')
