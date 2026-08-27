-- fp06 solution A: buffer the inflow (the seductive PARTIAL fix).
--
-- The same inline chest splice as Lab 4: inserter -> wooden chest ->
-- inserter replacing three belt tiles just upstream of the constraint.
-- With M1 (37.5/min) no longer blocked by M2 (30/min), the line's INTAKE
-- keeps up with the 36/min supplier -- warehouse overflow stops, and the
-- supply-loss requirement PASSES. But the constraint still produces
-- 30/min against 33/min of demand: the service requirement still FAILS,
-- and every workpiece saved from the supplier's scrap heap piles up in
-- the chest instead. One dial fixed, the system still failing --
-- fisl compare will mark this run INFEASIBLE.
local surface = game.surfaces["nauvis"]
local removed = 0
for _, x in ipairs({-6.5, -5.5, -4.5}) do
  local belt = surface.find_entities_filtered{name = "transport-belt", position = {x, 0.5}, radius = 0.2}[1]
  if belt then belt.destroy() removed = removed + 1 end
end
if removed ~= 3 then rcon.print("solution-step-fail: expected 3 belt tiles to replace, removed " .. removed) return end
local ok, err = pcall(function()
  local a = surface.create_entity{name = "fast-inserter", position = {-6.5, 0.5}, direction = defines.direction.west, force = "player", raise_built = true}
  local chest = surface.create_entity{name = "wooden-chest", position = {-5.5, 0.5}, force = "player", raise_built = true}
  local b = surface.create_entity{name = "fast-inserter", position = {-4.5, 0.5}, direction = defines.direction.west, force = "player", raise_built = true}
  if not (a and chest and b) then error("buffer entities did not place") end
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
