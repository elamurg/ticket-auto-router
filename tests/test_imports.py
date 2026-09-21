from importlib import import_module


def test_router_imports() -> None:
    import_module("router")
