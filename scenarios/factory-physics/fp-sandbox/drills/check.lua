-- fp-sandbox drill check: read-only world predicates, executed by the
-- controller over RCON after the run COMPLETES. Prints one JSON document.
-- Transmission-safe: single logical line, no inline comments, < 3500 chars.
-- The baseline belt count (18) must match the LABSANDBOX layout; a unit
-- test cross-checks it against the builder.
local s = game.surfaces["nauvis"]
local area = {{-18, -16}, {18, 16}}
local function ents(name) return s.find_entities_filtered{area = area, name = name} end
local d = {}
local function drill(id, passed, detail) d[#d + 1] = {id = id, passed = passed and true or false, detail = detail} end
local belts = ents("transport-belt")
drill("d1_place_belts", #belts >= 22, #belts .. " belts in the zone (the line starts with 18; place at least 4 more)")
local turned = 0
for _, b in pairs(belts) do if b.direction ~= defines.direction.east then turned = turned + 1 end end
drill("d2_rotate_belt", turned > 0, turned .. " belts face off the east axis")
local spliced = false
local chests = {}
for _, n in pairs({"wooden-chest", "steel-chest"}) do
  for _, c in pairs(ents(n)) do chests[#chests + 1] = c end
end
for _, c in pairs(chests) do
  if #s.find_entities_filtered{position = c.position, radius = 1.2, name = "fast-inserter"} >= 2 then spliced = true end
end
drill("d3_chest_splice", spliced, spliced and "a chest has inserters on two sides" or "no chest with two adjacent inserters found")
local upgraded = false
for _, m in pairs(ents("assembling-machine-2")) do
  local r = m.get_recipe()
  if r and r.name == "fisl-machine-workpiece" then upgraded = true end
end
drill("d4_machine_swap", upgraded, upgraded and "an assembling-machine-2 runs the machining recipe" or "no assembling-machine-2 with the machining recipe")
local wires = {defines.wire_connector_id.circuit_red, defines.wire_connector_id.circuit_green}
local gated = false
for _, i in pairs(ents("fast-inserter")) do
  local cb = i.get_control_behavior()
  if cb and cb.valid and cb.circuit_enable_disable then
    for _, w in pairs(wires) do
      local ok, hit = pcall(function()
        local c = i.get_wire_connector(w, false)
        return c ~= nil and #c.connections > 0
      end)
      if ok and hit then gated = true end
    end
  end
end
drill("d5_enable_condition", gated, gated and "a wired inserter has an enable condition" or "no wired inserter with an enable condition")
local dec_wires = {defines.wire_connector_id.combinator_input_red, defines.wire_connector_id.combinator_input_green, defines.wire_connector_id.combinator_output_red, defines.wire_connector_id.combinator_output_green}
local dec_nets = {}
for _, e in pairs(ents("decider-combinator")) do
  for _, w in pairs(dec_wires) do
    local ok, id = pcall(function()
      local c = e.get_wire_connector(w, false)
      return c and c.network_id or nil
    end)
    if ok and id then dec_nets[id] = true end
  end
end
local paired = false
for _, e in pairs(ents("constant-combinator")) do
  for _, w in pairs(wires) do
    local ok, id = pcall(function()
      local c = e.get_wire_connector(w, false)
      return c and c.network_id or nil
    end)
    if ok and id and dec_nets[id] then paired = true end
  end
end
drill("d6_combinator_pair", paired, paired and "a constant and a decider combinator share a circuit network" or "no constant+decider pair on one network")
rcon.print(helpers.table_to_json({drills = d}))
