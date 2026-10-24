"""Explicitly allowed safe demo tools, not arbitrary remote execution."""
def echo(payload):
    return {"echo": str(payload.get("text",""))[:500]}

def add(payload):
    numbers = payload.get("numbers",[])
    if not isinstance(numbers,list) or not 1 <= len(numbers) <= 100:
        raise ValueError("numbers must contain 1 to 100 items")
    if any(type(v) not in (int,float) or not -1e6 <= v <= 1e6 for v in numbers):
        raise ValueError("numbers must be bounded finite numbers")
    return {"total":sum(numbers)}

HANDLERS={"core.echo":echo,"core.add":add}
def dispatch(name,payload):
    if name not in HANDLERS: raise ValueError("Handler not allowed")
    return HANDLERS[name](payload)
