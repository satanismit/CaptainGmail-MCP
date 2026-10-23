import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth import authenticate_gmail

try:
    creds = authenticate_gmail()
    print("TOKEN IS VALID:", creds.valid)
except Exception as e:
    import traceback
    traceback.print_exc()
