import threading
import json as _json


SAFE_BUILTINS = {
    "__import__": __import__,
    "print": print,
    "json": _json,
    "dict": dict,
    "list": list,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "sorted": sorted,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "isinstance": isinstance,
    "type": type,
    "True": True,
    "False": False,
    "None": None,
}


class ScriptTimeout(Exception):
    pass


def _timeout_handler():
    raise ScriptTimeout("Script execution timed out (30s)")


def execute_script(script: str, request_data: dict | None = None, request_headers: dict | None = None, request_params: dict | None = None) -> dict:
    """Execute a user-provided Python script in a sandboxed environment.

    Injected variables:
      request_data    — parsed request body (dict, default {})
      request_headers — incoming request headers (dict, default {})
      request_params  — query / path parameters (dict, default {})
      response        — pre-initialized empty dict; script writes its result here

    Returns:
      {"ok": True, "data": response} on success
      {"ok": False, "error": "...", "status": 500} on failure
    """
    namespace = {
        "__builtins__": SAFE_BUILTINS,
        "request_data": request_data or {},
        "request_headers": request_headers or {},
        "request_params": request_params or {},
        "response": {},
    }

    timer = threading.Timer(30, _timeout_handler)
    try:
        timer.start()
        exec(script, namespace)
        timer.cancel()
    except ScriptTimeout:
        return {"ok": False, "error": "Script execution timed out (30s)", "status": 504}
    except Exception as exc:
        timer.cancel()
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "status": 500}
    finally:
        timer.cancel()

    response_data = namespace.get("response") or {}

    if "ok" in response_data and "status" in response_data:
        return response_data

    return {"ok": True, "data": response_data, "status": 200}
