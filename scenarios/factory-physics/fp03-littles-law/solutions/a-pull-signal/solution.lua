-- fp03 solution A: pull signal on the source inserter (v3).
--
-- Wires the source-side inserter (-43.5) to the LAST belt tile before
-- machine 1's input pickup (-33.5): the queue always forms immediately
-- upstream of the bottleneck, so that is where the gate must watch.
-- Condition "< 2" keeps at most ~2 workpieces staged at the machine, which
-- covers the ~4.8 s belt transit so the bottleneck never starves.
--
-- Version history is course material (see README):
-- v1 monitored a tile near the SOURCE: WIP only dropped ~19% because
--   everything downstream of the monitored tile still packed solid.
-- v2 wired directly to the right tile, 10.0 tiles away -- past the 9-tile
--   circuit wire reach. connect_to() returns false WITHOUT raising, the
--   unconnected inserter ignores its enable condition entirely, and the
--   run came out bit-identical to the baseline. Silent no-ops are worse
--   than loud failures: v3 relays through the belt at -38.5 (5.0 tiles to
--   each neighbor) and fails the step on any false return.
local surface = game.surfaces["nauvis"]
local function grab(name, x)
  return surface.find_entities_filtered{name = name, position = {x, 0.5}, radius = 0.4}[1]
end
local inserter = grab("fast-inserter", -43.5)
local relay = grab("transport-belt", -38.5)
local gate = grab("transport-belt", -33.5)
if not (inserter and relay and gate) then rcon.print("solution-step-fail: line entities not found") return end
local red = defines.wire_connector_id.circuit_red
local ok, err = pcall(function()
  local hop1 = inserter.get_wire_connector(red, true).connect_to(relay.get_wire_connector(red, true))
  local hop2 = relay.get_wire_connector(red, true).connect_to(gate.get_wire_connector(red, true))
  if not hop1 then error("wire inserter->relay did not connect (reach?)") end
  if not hop2 then error("wire relay->gate did not connect (reach?)") end
  local relay_cb = relay.get_or_create_control_behavior()
  relay_cb.circuit_enable_disable = false
  relay_cb.read_contents = false
  local gate_cb = gate.get_or_create_control_behavior()
  gate_cb.circuit_enable_disable = false
  gate_cb.read_contents = true
  gate_cb.read_contents_mode = defines.control_behavior.transport_belt.content_read_mode.hold
  local inserter_cb = inserter.get_or_create_control_behavior()
  inserter_cb.circuit_enable_disable = true
  inserter_cb.circuit_condition = { comparator = "<", first_signal = { type = "item", name = "fisl-rough-workpiece" }, constant = 2 }
  local a = inserter.get_wire_connector(red, true)
  local b = gate.get_wire_connector(red, true)
  local same_ok, same = pcall(function() return a.network_id == b.network_id end)
  if same_ok and not same then error("inserter and gate belt are on different circuit networks") end
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
