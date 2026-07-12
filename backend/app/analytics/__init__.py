"""AI-native analytics package for Data Mantri.

Modules in this package are intentionally small facades over production services so
the analytics architecture has a stable enterprise boundary while existing FastAPI
routes, auth, billing, and persistence continue to work unchanged.
"""

