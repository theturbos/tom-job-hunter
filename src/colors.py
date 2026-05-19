"""
colors.py — ANSI colors, cross-platform.
Strategy:
  - Windows Terminal / PS 6+ → ANSI works natively
  - Windows CMD / old PS → try colorama.just_fix_windows_console()
  - macOS / Linux → ANSI works natively
  - If all fails → plain text output (no color codes)
"""
import sys
import os

_ENABLED = True  # assume ANSI works by default

if sys.platform == "win32":
    # Windows Terminal (WT_SESSION) or PowerShell 6+ (PSModulePath) → ANSI ok
    if os.environ.get("WT_SESSION") or os.environ.get("PSModulePath"):
        _ENABLED = True
    else:
        # Try colorama for old CMD / PS5
        try:
            import colorama
            colorama.just_fix_windows_console()
            _ENABLED = True
        except ImportError:
            # Auto-install colorama if possible (one-liner setup)
            try:
                import subprocess
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", "--no-input", "colorama>=0.4.6"],
                    capture_output=True, timeout=60, check=True,
                )
                import colorama
                colorama.just_fix_windows_console()
                _ENABLED = True
            except Exception:
                # Final fallback: no colors
                _ENABLED = False


# ── Core helpers ───────────────────────────────────────────────

def _color(code: str, text: str) -> str:
    """Wrap text in ANSI escape if colors are enabled."""
    if _ENABLED:
        return f"\033[{code}m{text}\033[0m"
    return str(text)


# ── Public API (namespaced for clean imports) ──────────────────

def green(text: str) -> str:
    return _color("32", text)


def red(text: str) -> str:
    return _color("31", text)


def yellow(text: str) -> str:
    return _color("33", text)


def cyan(text: str) -> str:
    return _color("36", text)


def bold(text: str) -> str:
    return _color("1", text)


def dim(text: str) -> str:
    return _color("2", text)


def italic(text: str) -> str:
    return _color("3", text)


def bar() -> str:
    """Horizontal separator bar."""
    return cyan(bold("─" * 60)) if _ENABLED else "=" * 60
