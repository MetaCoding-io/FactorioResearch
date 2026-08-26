-- fp04 solution B: relieve the constraint itself.
--
-- Replaces the middle assembling-machine-1 (1s inspect / 0.5 speed = 2.0s
-- per craft, the system constraint) with an assembling-machine-3 (0.8s per
-- craft). Throughput rises until the NEXT constraint binds (M1 at 1.6s per
-- craft -> 37.5/min); the blocked/starved signature moves with the
-- constraint. Only relieving the constraint raises throughput -- a buffer
-- never does.
--
-- Applied before start: the destroyed machine leaves the entity set at
-- boundary 0 with empty eligibility, and the replacement (raise_built)
-- joins at boundary 0 -- dynamic membership (ADR 0016) keeps the pooled
-- denominators honest through the swap.
local surface = game.surfaces["nauvis"]
local old = surface.find_entities_filtered{name = "assembling-machine-1", position = {0.5, 0.5}, radius = 0.4}[1]
if old == nil then rcon.print("solution-step-fail: constraint machine not found at (0.5, 0.5)") return end
old.destroy{raise_destroy = true}
local ok, err = pcall(function()
  local machine = surface.create_entity{name = "assembling-machine-3", position = {0.5, 0.5}, force = "player", raise_built = true}
  if machine == nil then error("assembling-machine-3 did not place") end
  machine.set_recipe("fisl-inspect-workpiece")
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
