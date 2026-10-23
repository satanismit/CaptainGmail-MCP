import sys
sys.path.insert(0, '.')
import api
print('api.py imports OK')
print('Templates count:', len(api.PROMPT_TEMPLATES))
for name in api.PROMPT_TEMPLATES:
    print(f'  - {name}')
print()
print('Has Action Items & Follow-ups:', 'Action Items & Follow-ups' in api.PROMPT_TEMPLATES)

import ai_service
print('\nai_service.py imports OK')
print('VALID_TONES:', ai_service.VALID_TONES)
print('WRITE_TOOLS:', ai_service.WRITE_TOOLS)
