-- Conserved workpiece family (ADR 0005 §4, PRD §27).
--
-- Each transformation preserves exactly one logical workpiece (1 -> 1).
-- No productivity, probabilistic outputs, or quality transformations are
-- permitted in these canonical recipes (ADR 0005 §12).
--
-- POC icons reuse base-game art with tints so the mod needs no bundled
-- graphics; dedicated art is later content polish.

local function workpiece_item(name, order, base_icon, tint)
  return {
    type = "item",
    name = name,
    icons = {
      {
        icon = base_icon,
        icon_size = 64,
        tint = tint,
      },
    },
    subgroup = "intermediate-product",
    order = "z[fisl]-" .. order,
    stack_size = 100,
  }
end

local function conserving_recipe(name, order, ingredient, result, seconds)
  return {
    type = "recipe",
    name = name,
    category = "crafting",
    enabled = true,
    energy_required = seconds,
    ingredients = { { type = "item", name = ingredient, amount = 1 } },
    results = { { type = "item", name = result, amount = 1 } },
    allow_productivity = false,
    order = "z[fisl]-" .. order,
  }
end

data:extend({
  workpiece_item("fisl-rough-workpiece", "a", "__base__/graphics/icons/iron-plate.png", { r = 0.8, g = 0.6, b = 0.4, a = 1 }),
  workpiece_item("fisl-machined-workpiece", "b", "__base__/graphics/icons/iron-gear-wheel.png", { r = 0.7, g = 0.7, b = 0.9, a = 1 }),
  workpiece_item("fisl-inspected-workpiece", "c", "__base__/graphics/icons/iron-gear-wheel.png", { r = 0.5, g = 0.9, b = 0.5, a = 1 }),
  workpiece_item("fisl-finished-workpiece", "d", "__base__/graphics/icons/steel-plate.png", { r = 0.9, g = 0.85, b = 0.3, a = 1 }),

  conserving_recipe("fisl-machine-workpiece", "a", "fisl-rough-workpiece", "fisl-machined-workpiece", 2),
  conserving_recipe("fisl-inspect-workpiece", "b", "fisl-machined-workpiece", "fisl-inspected-workpiece", 1),
  conserving_recipe("fisl-finish-workpiece", "c", "fisl-inspected-workpiece", "fisl-finished-workpiece", 1),
})
