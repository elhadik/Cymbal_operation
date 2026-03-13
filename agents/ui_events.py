import asyncio

_events = {}
_ui_queues = {}

def get_scan_complete_event():
    loop = asyncio.get_running_loop()
    if loop not in _events:
        _events[loop] = asyncio.Event()
    return _events[loop]

def get_ui_queue():
    loop = asyncio.get_running_loop()
    if loop not in _ui_queues:
        _ui_queues[loop] = asyncio.Queue()
    return _ui_queues[loop]
