-- fp06 solution B: relieve the constraint (the system fix).
--
-- Replaces the middle assembling-machine-1 (2.0s per craft, 30/min - the
-- constraint) with an assembling-machine-2 (1.33s, 45/min). The line's
-- pace moves to M1 at 37.5/min, which covers BOTH external constraints at
-- once: intake >= the 36/min supplier schedule (warehouse stops
-- overflowing -> supply requirement passes) and output >= the 33/min
-- customer (service requirement passes). One move, both requirements --
-- because both symptoms shared one cause. The machine swap flows through
-- dynamic entity-set membership (ADR 0016): the removed machine's
-- eligibility ends, the replacement's begins at boundary 0.
local surface = game.surfaces["nauvis"]
local old = surface.find_entities_filtered{name = "assembling-machine-1", position = {0.5, 0.5}, radius = 0.4}[1]
if old == nil then rcon.print("solution-step-fail: constraint machine not found at (0.5, 0.5)") return end
old.destroy{raise_destroy = true}
local ok, err = pcall(function()
  local machine = surface.create_entity{name = "assembling-machine-2", position = {0.5, 0.5}, force = "player", raise_built = true}
  if machine == nil then error("assembling-machine-2 did not place") end
  machine.set_recipe("fisl-inspect-workpiece")
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
