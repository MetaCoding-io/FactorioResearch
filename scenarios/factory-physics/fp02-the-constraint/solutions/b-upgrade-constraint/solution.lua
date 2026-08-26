-- fp02 solution B: upgrade THE constraint.
--
-- Replaces the middle machine (assembling-machine-1 at 0.5, 1s inspect /
-- 0.5 speed = 2.0s per craft -- the constraint) with an
-- assembling-machine-2 (1.33s per craft). Throughput rises until the NEXT
-- constraint binds: the upstream machine at 1.6s per craft caps the line
-- at 37.5/min. Same class of action as solution A; entirely different
-- system result -- the only difference is WHERE.
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
