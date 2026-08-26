-- fp05 solution B: the over-tight pull (deliberately WRONG).
--
-- A combinator clock throttles admission to ~10/min against 12/min of
-- customer demand: a constant combinator feeds signal-T=1 into a
-- self-looped decider (T < 360 -> pass the running count), so T ramps
-- 0..359 and resets; the source inserter is enabled only while T < 20 --
-- a window shorter than one full inserter swing, so exactly one workpiece
-- is admitted per 360-tick cycle (10/min).
--
-- Result: WIP collapses to nearly nothing -- and the backlog grows by
-- ~2/min forever. On-time rate craters, the p95 wait is CENSORED (demand
-- that was never served has no measurable wait), and no later heroics can
-- un-miss a deadline. "Low WIP is not success if the customer is not
-- served."
--
-- First scripted use of 2.0 combinator control behaviors: parameters are
-- set in the 2.0 formats and the step fails loudly if the runtime rejects
-- them (no silent fallbacks; see fp03 v2's lesson).
local surface = game.surfaces["nauvis"]
local inserter = surface.find_entities_filtered{name = "fast-inserter", position = {-43.5, 0.5}, radius = 0.4}[1]
if inserter == nil then rcon.print("solution-step-fail: source inserter not found") return end
local ok, err = pcall(function()
  local constant = surface.create_entity{name = "constant-combinator", position = {-42.5, -2.5}, force = "player", raise_built = true}
  local decider = surface.create_entity{name = "decider-combinator", position = {-40.5, -2.5}, direction = defines.direction.east, force = "player", raise_built = true}
  if not (constant and decider) then error("combinators did not place") end
  local signal_t = { type = "virtual", name = "signal-T", quality = "normal" }
  local constant_cb = constant.get_or_create_control_behavior()
  local section = constant_cb.sections[1] or constant_cb.add_section()
  section.set_slot(1, { value = signal_t, min = 1 })
  local decider_cb = decider.get_or_create_control_behavior()
  decider_cb.parameters = {
    conditions = { { first_signal = signal_t, comparator = "<", constant = 360 } },
    outputs = { { signal = signal_t, copy_count_from_input = true } },
  }
  local red = defines.wire_connector_id.circuit_red
  local input_red = defines.wire_connector_id.combinator_input_red
  local output_red = defines.wire_connector_id.combinator_output_red
  local feed = constant.get_wire_connector(red, true).connect_to(decider.get_wire_connector(input_red, true))
  local loop = decider.get_wire_connector(output_red, true).connect_to(decider.get_wire_connector(input_red, true))
  local drive = decider.get_wire_connector(output_red, true).connect_to(inserter.get_wire_connector(red, true))
  if not feed then error("wire constant->decider did not connect") end
  if not loop then error("decider self-loop did not connect") end
  if not drive then error("wire decider->inserter did not connect (reach?)") end
  local inserter_cb = inserter.get_or_create_control_behavior()
  inserter_cb.circuit_enable_disable = true
  inserter_cb.circuit_condition = { comparator = "<", first_signal = signal_t, constant = 20 }
end)
if not ok then rcon.print("solution-step-fail: " .. tostring(err)) return end
rcon.print("solution-step-ok")
