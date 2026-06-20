"""Shared SlowAPI limiter — must be the same instance used by main.py and route decorators."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
