-- fp07 CONWIP gate, step 1/3: build the ledger-in-circuits.
-- Two tap belts count admissions (+1) and completions (-1) as item
-- pulses; two arithmetic combinators convert the pulses to signal-W; a
-- self-looped decider accumulates them. The running sum IS the line's
-- WIP: the same quantity FISL's conservation ledger tracks, rebuilt from
-- wire. Step 3 turns it into a cap on the source inserter.
local surface = game.surfaces["nauvis"]
local function grab(name, x, y)
  return surface.find_entities_filtered{name = name, position = {x, y}, radius = 0.4}[1]
end
local adm_tap = grab("transport-belt", -42.5, 0.5)
local com_tap = grab("transport-belt", 42.5, 0.5)
if not (adm_tap and com_tap) then rcon.print("solution-step-fail: tap belts not found") return end
local W = { type = "virtual", name = "signal-W", quality = "normal" }
local ok, err = pcall(function()
  local arith_a = surface.create_entity{name = "arithmetic-combinator", position = {-41.5, -2.5}, direction = defines.direction.east, force = "player", raise_built = true}
  local arith_n = surface.create_entity{name = "arithmetic-combinator", position = {41.5, -2.5}, direction = defines.direction.west, force = "player", raise_built = true}
  local memory = surface.create_entity{name = "decider-combinator", position = {-38.5, -2.5}, direction = defines.direction.east, force = "player", raise_built = true}
  if not (arith_a and arith_n and memory) then error("combinators did not place") end
  local pulse = defines.control_behavior.transport_belt.content_read_mode.pulse
  for _, tap in pairs({adm_tap, com_tap}) do
    local cb = tap.get_or_create_control_behavior()
    cb.circuit_enable_disable = false
    cb.read_contents = true
    cb.read_contents_mode = pulse
  end
  arith_a.get_or_create_control_behavior().parameters = { first_signal = { type = "item", name = "fisl-rough-workpiece", quality = "normal" }, operation = "*", second_constant = 1, output_signal = W }
  arith_n.get_or_create_control_behavior().parameters = { first_signal = { type = "item", name = "fisl-finished-workpiece", quality = "normal" }, operation = "*", second_constant = -1, output_signal = W }
  memory.get_or_create_control_behavior().parameters = { conditions = { { first_signal = W, comparator = "<", constant = 2000000000 } }, outputs = { { signal = W, copy_count_from_input = true } } }
  local g = defines.wire_connector_id.circuit_green
  local ig = defines.wire_connector_id.combinator_input_green
  local ir = defines.wire_connector_id.combinator_input_red
  local outr = defines.wire_connector_id.combinator_output_red
  if not adm_tap.get_wire_connector(g, true).connect_to(arith_a.get_wire_connector(ig, true)) then error("admission tap wire") end
  if not com_tap.get_wire_connector(g, true).connect_to(arith_n.get_wire_connector(ig, true)) then error("completion tap wire") end
  if not arith_a.get_wire_connector(outr, true).connect_to(memory.get_wire_connector(ir, true)) then error("arith to memory wire") end
  if not memory.get_wire_connector(outr, true).connect_to(memory.get_wire_connector(ir, true)) then error("memory self loop") end
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
