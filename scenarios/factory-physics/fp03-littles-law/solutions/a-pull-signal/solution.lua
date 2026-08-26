-- fp03 solution A: pull signal on the source inserter (v2).
--
-- Wires the source-side inserter to the LAST belt tile before machine 1's
-- input pickup (-33.5): the queue always forms immediately upstream of the
-- bottleneck, so that is where the gate must watch. Condition "< 2" keeps
-- at most ~2 workpieces staged at the machine, which covers the ~4.8 s
-- belt transit so the bottleneck never starves (feed capacity ~22/min vs
-- 15/min demand).
--
-- v1 of this solution monitored a tile near the SOURCE and only cut WIP by
-- ~19%: everything downstream of the monitored tile still packed solid.
-- Gate placement is the lesson — see the solution README.
--
-- Control-behavior property names differ slightly across 2.0 point
-- releases; both spellings are attempted and the step fails loudly if
-- neither takes effect.
local surface = game.surfaces["nauvis"]
local inserter = surface.find_entities_filtered{name = "fast-inserter", position = {-43.5, 0.5}, radius = 0.4}[1]
local belt = surface.find_entities_filtered{name = "transport-belt", position = {-33.5, 0.5}, radius = 0.4}[1]
if inserter == nil or belt == nil then rcon.print("solution-step-fail: source inserter or gate belt not found") return end
local red = defines.wire_connector_id.circuit_red
local ok, err = pcall(function()
  inserter.get_wire_connector(red, true).connect_to(belt.get_wire_connector(red, true))
  local belt_cb = belt.get_or_create_control_behavior()
  belt_cb.read_contents = true
  belt_cb.read_contents_mode = defines.control_behavior.transport_belt.content_read_mode.hold
  local inserter_cb = inserter.get_or_create_control_behavior()
  local enabled = pcall(function() inserter_cb.circuit_enable_disable = true end)
  local enabled2 = pcall(function() inserter_cb.circuit_enabled = true end)
  if not (enabled or enabled2) then error("could not enable circuit control on inserter") end
  local condition = { comparator = "<", first_signal = { type = "item", name = "fisl-rough-workpiece" }, constant = 2 }
  local set1 = pcall(function() inserter_cb.circuit_condition = condition end)
  if not set1 then
    local set2 = pcall(function() inserter_cb.circuit_condition = { condition = condition } end)
    if not set2 then error("could not set circuit condition on inserter") end
  end
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
