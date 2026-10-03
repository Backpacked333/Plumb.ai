"""Plumb Autonomous Implementation System: reference package.

This package contains typed contracts, a local reference checker, a SQLite
effect-ledger simulation and aggregate state machines for the Plumb
specification v0.2 (October 2, 2026). It is a reference implementation of
selected controls, not a deployed product: nothing here connects to customer
systems, calls a model, trains weights or provisions infrastructure.
"""

SPEC_VERSION = "0.2"
SPEC_DATE = "2026-10-02"
PACKAGE_VERSION = "0.2.0"

__all__ = ["SPEC_VERSION", "SPEC_DATE", "PACKAGE_VERSION"]
