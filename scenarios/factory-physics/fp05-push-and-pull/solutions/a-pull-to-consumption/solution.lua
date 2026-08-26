-- fp05 solution A: pull admission to consumption (Lab 3's gate, kept).
--
-- Identical mechanics to fp03's proven v3 pull gate: red wire from the
-- source inserter (-43.5) relayed through the belt at -38.5 to the gate
-- belt at -33.5 (circuit wire reaches 9 tiles; the direct span is 10);
-- gate reads contents (hold), inserter enabled while rough < 2.
--
-- Under customer demand the point is what the gate does NOT do: it paces
-- admission to the bottleneck's consumption (15/min), which still exceeds
-- demand (12/min), so the customer is served exactly as well as under
-- push -- with a fraction of the inventory. WIP control and service are
-- not opposites when capacity covers demand.
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
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
