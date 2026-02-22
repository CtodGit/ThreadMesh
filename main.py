#!/usr/bin/env python3
# ThreadMesh - root-level launcher shim
# Delegates to the real entry point: threadmesh/main.py
# Usage: python main.py  (from project root)

from threadmesh.main import main

if __name__ == "__main__":
    main()
