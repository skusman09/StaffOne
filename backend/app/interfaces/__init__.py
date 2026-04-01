"""
Interface definitions (Protocol classes) for the StaffOne backend.

These Protocols define the contracts that repository and service implementations
must satisfy. Using Python's structural typing (PEP 544), any class that implements
the required methods satisfies the protocol — no explicit inheritance needed.

This enables:
- Dependency Inversion: services depend on abstractions, not concrete classes
- Testability: pass mock implementations without monkey-patching
- Extensibility: swap implementations (e.g., cached repo) without touching services
"""
