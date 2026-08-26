-- fp04 solution A: buffer chest spliced into the M1 -> M2 segment.
--
-- Replaces three belt tiles just upstream of the constraint with
-- inserter -> wooden chest -> inserter (all on the line row, reusing the
-- proven west-facing convention: pick west tile, drop east tile). The
-- chest absorbs M1's surplus, so M1's blocked time collapses and its
-- productive fraction rises -- while system throughput does not move
-- (M2 is still the constraint) and WIP grows for the whole run.
-- "Local productive time is not the system objective."
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
