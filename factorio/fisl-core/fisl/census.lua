-- Physical census: independent ledger validation + "where is the WIP?"
-- decomposition (ADR 0017 §6-§10). Runs at the configured cadence, never
-- rewrites the ledger, and flags a conservative validity interval on
-- discrepancy (ADR 0017 §9).
--
-- Holder adapters here are exactly the runtime hypotheses tracked by
-- RV-004 (belt dedup) and RV-005 (active-craft continuity).

local util = require("fisl.util")
local state = require("fisl.state")
local telemetry = require("fisl.telemetry")
local ledger = require("fisl.ledger")

local census = {}

function census.init(config)
  local s = state.get()
  s.census = {}
  for _, plan in ipairs(config.resolved.observation_plan.census or {}) do
    s.census[plan.metric] = {
      flow = plan.flow,
      every_ticks = plan.every_ticks,
      tolerance = plan.discrepancy_tolerance,
      include_player_inventory = plan.include_player_inventory,
      last_good_tick = nil,       -- most recent agreeing census boundary
      discrepancy_intervals = {}, -- { {from_tick, to_tick, delta} }
      coverage_incomplete_count = 0,
    }
  end
end

local function zone_area(config, flow)
  local system = config.resolved.systems[config.resolved.flows[flow].system]
  local zone = config.resolved.zones[system.primary_zone]
  return zone.surface, {
    { zone.area.left_top[1], zone.area.left_top[2] },
    { zone.area.right_bottom[1], zone.area.right_bottom[2] },
  }
end

local function in_zone(zone, position)
  return position.x >= zone[1][1] and position.x < zone[2][1]
    and position.y >= zone[1][2] and position.y < zone[2][2]
end

local function is_port_apparatus(s, entity)
  if entity.unit_number == nil then return false end
  for _, port in pairs(s.ports) do
    if port.unit_number == entity.unit_number then return true end
  end
  return false
end

--- Count tracked work units for one flow by physical holder category.
--- Returns (decomposition, total, coverage_ok).
function census.take(config, flow_id, include_player_inventory)
  local s = state.get()
  local led = s.ledgers[flow_id]
  local surface_name, area = zone_area(config, flow_id)
  local surface = game.surfaces[surface_name]
  if surface == nil then return nil, 0, false end

  local decomposition = {
    containers = 0, machine_inventories = 0, active_crafts = 0,
    belts = 0, inserter_hands = 0, ground = 0, player_inventory = 0,
  }
  local coverage_ok = true

  local function count_tracked(get_count)
    local total = 0
    for item, coefficient in pairs(led.coefficients) do
      total = total + get_count(item) * coefficient
    end
    return total
  end

  -- Containers (excluding FISL port apparatus, ADR 0002 §9 / ADR 0016 §9).
  for _, entity in ipairs(surface.find_entities_filtered({ area = area, type = { "container", "logistic-container" } })) do
    if in_zone(area, entity.position) and not is_port_apparatus(s, entity) then
      local inventory = entity.get_inventory(defines.inventory.chest)
      decomposition.containers = decomposition.containers
        + count_tracked(function(item) return inventory.get_item_count(item) end)
    end
  end

  -- Crafting machines: process inventories + active-craft occupancy (RV-005).
  for _, entity in ipairs(surface.find_entities_filtered({ area = area, type = { "assembling-machine", "furnace" } })) do
    if in_zone(area, entity.position) then
      local input = entity.get_inventory(util.crafter_input_define())
      local output = entity.get_inventory(util.crafter_output_define())
      for _, inventory in ipairs({ input, output }) do
        if inventory then
          decomposition.machine_inventories = decomposition.machine_inventories
            + count_tracked(function(item) return inventory.get_item_count(item) end)
        end
      end
      -- Active craft: for validated conserved 1:1 recipes the committed work
      -- equals the tracked-ingredient quantity of one craft (ADR 0005 §11).
      local ok, crafting = pcall(function() return entity.is_crafting() end)
      if ok and crafting then
        local recipe = entity.get_recipe()
        if recipe then
          for _, ingredient in ipairs(recipe.ingredients) do
            local coefficient = led.coefficients[ingredient.name]
            if coefficient then
              decomposition.active_crafts = decomposition.active_crafts
                + (ingredient.amount or 1) * coefficient
            end
          end
        end
      end
    end
  end

  -- Belts (ADR 0005 §13, RV-004). Empirical 2.0.77 semantics: each entity's
  -- LuaTransportLine holds only that entity's own segment contents, so the
  -- naive per-entity/per-line sum is already exact. line_equals-based
  -- deduplication is WRONG here — it reports true for different segments of
  -- the same merged belt line group and silently drops their contents
  -- (observed: 15 physical items counted as 8 on a 4-belt straight run).
  for _, entity in ipairs(surface.find_entities_filtered({
    area = area, type = { "transport-belt", "underground-belt", "splitter", "loader", "linked-belt" },
  })) do
    if in_zone(area, entity.position) then
      local max_index = entity.get_max_transport_line_index()
      for index = 1, max_index do
        local contents = entity.get_transport_line(index).get_contents()
        decomposition.belts = decomposition.belts
          + count_tracked(function(item) return util.contents_count(contents, item) end)
      end
    end
  end

  -- Inserter hands (ADR 0005 §14 as census category).
  for _, entity in ipairs(surface.find_entities_filtered({ area = area, type = "inserter" })) do
    if in_zone(area, entity.position) then
      local stack = entity.held_stack
      if stack and stack.valid_for_read then
        local coefficient = led.coefficients[stack.name]
        if coefficient then
          decomposition.inserter_hands = decomposition.inserter_hands + stack.count * coefficient
        end
      end
    end
  end

  -- Ground items (ADR 0017 §13).
  for _, entity in ipairs(surface.find_entities_filtered({ area = area, type = "item-entity" })) do
    if in_zone(area, entity.position) and entity.stack and entity.stack.valid_for_read then
      local coefficient = led.coefficients[entity.stack.name]
      if coefficient then
        decomposition.ground = decomposition.ground + entity.stack.count * coefficient
      end
    end
  end

  -- Player-held admitted work remains WIP (ADR 0017 §11).
  if include_player_inventory then
    for _, player in pairs(game.players) do
      local inventory = player.get_main_inventory and player.get_main_inventory() or nil
      if inventory then
        local held = count_tracked(function(item) return inventory.get_item_count(item) end)
        if held > 0 then
          decomposition.player_inventory = decomposition.player_inventory + held
          local s2 = state.get()
          s2.validity.manual_carriage_seen = true
        end
      end
      if player.cursor_stack and player.cursor_stack.valid_for_read then
        local coefficient = led.coefficients[player.cursor_stack.name]
        if coefficient then
          decomposition.player_inventory = decomposition.player_inventory
            + player.cursor_stack.count * coefficient
        end
      end
    end
  end

  local total = 0
  for _, quantity in pairs(decomposition) do total = total + quantity end
  return decomposition, total, coverage_ok
end

--- Run cross-checks due at prepared boundary T (pipeline step 9).
function census.cross_check(config, experiment_tick)
  census._run_checks(config, experiment_tick, false)
end

--- Unconditional cross-check, used at the final experiment boundary
--- (ADR 0017 §6: a census is required at the final boundary).
function census.cross_check_forced(config, experiment_tick)
  census._run_checks(config, experiment_tick, true)
end

function census._run_checks(config, experiment_tick, forced)
  local s = state.get()
  for metric_id, entry in pairs(s.census) do
    if forced or experiment_tick % entry.every_ticks == 0 then
      local decomposition, total, coverage_ok = census.take(config, entry.flow, entry.include_player_inventory)
      local ledger_wip = ledger.wip(entry.flow)
      if not coverage_ok or decomposition == nil then
        entry.coverage_incomplete_count = entry.coverage_incomplete_count + 1
        telemetry.emit({
          type = "wip_census_coverage_incomplete", metric = metric_id,
          experiment_tick = experiment_tick,
        })
      else
        local delta = total - ledger_wip
        telemetry.emit({
          type = "wip_census", metric = metric_id, flow = entry.flow,
          experiment_tick = experiment_tick,
          ledger_wip = ledger_wip, census_wip = total, discrepancy = delta,
          decomposition = decomposition, method = "physical_census",
        })
        if math.abs(delta) > entry.tolerance then
          -- Conservative validity interval since the prior good check
          -- (ADR 0017 §9); the ledger is never rewritten (§8).
          local from_tick = entry.last_good_tick or 0
          entry.discrepancy_intervals[#entry.discrepancy_intervals + 1] = {
            from_tick = from_tick, to_tick = experiment_tick, delta = delta,
          }
          telemetry.emit({
            type = "wip_census_discrepancy", metric = metric_id, flow = entry.flow,
            experiment_tick = experiment_tick, discrepancy = delta,
            suspect_from_tick = from_tick, suspect_to_tick = experiment_tick,
          })
        else
          entry.last_good_tick = experiment_tick
        end
      end
    end
  end
end

return census
