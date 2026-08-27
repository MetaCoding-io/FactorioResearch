-- fp07 CONWIP gate, step 2/3: carry the completion pulses home.
-- The negated pulses at the sink must reach the memory near the source,
-- 80 tiles away against a 9-tile wire reach. Relay red wire along the
-- line's own belts (read disabled, so relays add nothing to the signal),
-- checking every hop: fp03 v2's silent-reach lesson, institutionalized.
local surface = game.surfaces["nauvis"]
local function grab(name, x, y)
  return surface.find_entities_filtered{name = name, position = {x, y}, radius = 0.4}[1]
end
local arith_n = grab("arithmetic-combinator", 41.5, -2.5)
local memory = grab("decider-combinator", -38.5, -2.5)
if not (arith_n and memory) then rcon.print("solution-step-fail: step-1 combinators not found") return end
local xs = {34.5, 26.5, 18.5, 10.5, 3.5, -2.5, -10.5, -18.5, -26.5, -33.5}
local r = defines.wire_connector_id.circuit_red
local ok, err = pcall(function()
  local prev = arith_n.get_wire_connector(defines.wire_connector_id.combinator_output_red, true)
  for _, x in pairs(xs) do
    local belt = grab("transport-belt", x, 0.5)
    if not belt then error("relay belt missing at x=" .. x) end
    local cb = belt.get_or_create_control_behavior()
    cb.circuit_enable_disable = false
    cb.read_contents = false
    local c = belt.get_wire_connector(r, true)
    if not prev.connect_to(c) then error("relay hop failed into x=" .. x) end
    prev = c
  end
  if not prev.connect_to(memory.get_wire_connector(defines.wire_connector_id.combinator_input_red, true)) then error("final hop to memory failed") end
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
