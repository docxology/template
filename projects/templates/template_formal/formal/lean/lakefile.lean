import Lake
open Lake DSL

-- Minimal lakefile for the optional formal side-spec. No mathlib dependency
-- so `lake build` stays fast (single small file, no external downloads).
package «ant_protocol» where

@[default_target]
lean_lib «AntProtocol» where
