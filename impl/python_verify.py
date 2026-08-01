"""
ΣLang P0 Foundations — Algorithmic Verification (Python Prototype)
Verifies all P0 modules: Time (§T), Error (§E), Confidence (§C), I/O (§I)
Total: 95 tests across 4 modules
"""

__version__ = "0.3.0"

# Re-export the verification runner
from verify_p0 import main

if __name__ == "__main__":
    main()
