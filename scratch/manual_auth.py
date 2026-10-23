import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth import authenticate_gmail

print("Starting Google Auth flow...")
try:
    authenticate_gmail()
    print("SUCCESS: token.json created!")
except Exception as e:
    import traceback
    traceback.print_exc()
