#!/usr/bin/env bash
# Wrapper für ElmerSolver in WSL.
# Ohne HWLOC_COMPONENTS=-gl hängt der OpenMPI-Hilfsprozess (orted) beim Abfragen von
# X11-Displays (connect auf 127.0.0.1:6001). Siehe docs/reviews/phase0_toolcheck.md.
# Aufruf: scripts/elmer.sh <case.sif>   (im Verzeichnis des Falls)
export HWLOC_COMPONENTS=-gl
exec ElmerSolver "$@"
