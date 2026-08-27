-- fp07 CONWIP gate, step 3/3: the cap. Enable the source inserter only
-- while the circuit ledger reads W < CAP. One number moves the whole
-- operating point along the characteristic curves.
local surface = game.surfaces["nauvis"]
local memory = surface.find_entities_filtered{name = "decider-combinator", position = {-38.5, -2.5}, radius = 0.4}[1]
local inserter = surface.find_entities_filtered{name = "fast-inserter", position = {-43.5, 0.5}, radius = 0.4}[1]
if not (memory and inserter) then rcon.print("solution-step-fail: memory or source inserter not found") return end
local W = { type = "virtual", name = "signal-W", quality = "normal" }
local ok, err = pcall(function()
  local g = defines.wire_connector_id.circuit_green
  local og = defines.wire_connector_id.combinator_output_green
  if not memory.get_wire_connector(og, true).connect_to(inserter.get_wire_connector(g, true)) then error("memory to inserter wire (reach?)") end
  local cb = inserter.get_or_create_control_behavior()
  cb.circuit_enable_disable = true
  cb.circuit_condition = { comparator = "<", first_signal = W, constant = 24 }
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
