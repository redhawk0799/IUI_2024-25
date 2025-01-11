
try:
    import teslasuit_sdk
except ImportError:
    import os
    import sys
    sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, sdk_path)
    import teslasuit_sdk
    print(f'Successfully added \'{sdk_path}\' into sys.path')
