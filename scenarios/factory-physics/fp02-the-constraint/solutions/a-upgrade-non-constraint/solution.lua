-- fp02 solution A: upgrade a NON-constraint (the futile upgrade).
--
-- Replaces the DOWNSTREAM fast machine (assembling-machine-2 at 11.5,
-- 1.33s per craft) with an assembling-machine-3 (0.8s per craft). It is a
-- real capacity upgrade to a real machine -- and system throughput does
-- not move, because the middle machine (2.0s per craft) still paces the
-- line. The upgraded machine simply starves harder.
local surface = game.surfaces["nauvis"]
local old = surface.find_entities_filtered{name = "assembling-machine-2", position = {11.5, 0.5}, radius = 0.4}[1]
if old == nil then rcon.print("solution-step-fail: downstream machine not found at (11.5, 0.5)") return end
old.destroy{raise_destroy = true}
local ok, err = pcall(function()
  local machine = surface.create_entity{name = "assembling-machine-3", position = {11.5, 0.5}, force = "player", raise_built = true}
  if machine == nil then error("assembling-machine-3 did not place") end
  machine.set_recipe("fisl-finish-workpiece")
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
