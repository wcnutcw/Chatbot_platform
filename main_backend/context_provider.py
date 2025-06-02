_context = ""

def set_context(ctx: str):
    global _context
    _context = ctx

def get_context() -> str:
    return _context
