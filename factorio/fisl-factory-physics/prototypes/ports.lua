-- FISL port apparatus prototypes (ADR 0003 §5, ADR 0017 §16).
--
-- Ports are controlled experimental equipment, not learner factory parts:
-- non-minable at the prototype level; runtime hardening additionally sets
-- destructible=false and operable=false on binding (fisl-core lifecycle).
-- Visual distinction currently comes from a tint over base chest graphics.

local util = require("util")

local function port_container(name, tint)
  local chest = util.table.deepcopy(data.raw["container"]["steel-chest"])
  chest.name = name
  chest.minable = nil
  -- One slot (= 100 workpieces): the port IS the declared warehouse, and a
  -- finite warehouse is what lets scheduled-supply congestion/loss become
  -- physical (ADR 0003; Lab 6). Replenish labs use target 100, which fits
  -- exactly; sinks settle every boundary and never accumulate.
  chest.inventory_size = 1
  if chest.icons == nil then
    chest.icons = { { icon = chest.icon, icon_size = chest.icon_size or 64 } }
    chest.icon = nil
  end
  for _, layer in ipairs(chest.icons) do
    layer.tint = tint
  end
  -- Tint the in-world sprite so learners can see it is FISL apparatus.
  if chest.picture and chest.picture.layers then
    chest.picture.layers[1].tint = tint
  end
  local item = util.table.deepcopy(data.raw["item"]["steel-chest"])
  item.name = name
  item.place_result = name
  item.icons = util.table.deepcopy(chest.icons)
  item.icon = nil
  item.order = "z[fisl]-" .. name
  return chest, item
end

local source_chest, source_item = port_container("fisl-source-port", { r = 0.35, g = 0.65, b = 1.0, a = 1 })
local sink_chest, sink_item = port_container("fisl-sink-port", { r = 1.0, g = 0.55, b = 0.25, a = 1 })

data:extend({ source_chest, source_item, sink_chest, sink_item })
