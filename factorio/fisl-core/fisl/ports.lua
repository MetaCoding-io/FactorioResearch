-- Material port runtime: binding, hardening, and per-tick settlement
-- (ADR 0003 §7-§9, ADR 0017 §16).

local util = require("fisl.util")
local state = require("fisl.state")
local telemetry = require("fisl.telemetry")
local schedules = require("fisl.schedules")

local ports = {}

local function chest_inventory(entity)
  return entity.get_inventory(defines.inventory.chest)
end

--- Resolve every configured port binding; returns nil on success or a list of
--- problems. Called during READY validation (FR-LIFE-001).
function ports.bind_all(config)
  local s = state.get()
  local problems = {}
  s.ports = {}
  for port_id, port_config in pairs(config.resolved.ports) do
    local surface = game.surfaces[port_config.binding.surface]
    if surface == nil then
      problems[#problems + 1] = "port " .. port_id .. ": unknown surface " .. port_config.binding.surface
    else
      local position = port_config.binding.position
      local found = surface.find_entities_filtered({
        name = port_config.binding.prototype,
        position = { position[1], position[2] },
        radius = 0.5,
      })
      if #found ~= 1 then
        problems[#problems + 1] = string.format(
          "port %s: expected exactly 1 %s at (%s,%s), found %d",
          port_id, port_config.binding.prototype, position[1], position[2], #found)
      else
        local entity = found[1]
        -- Hardening (ADR 0017 §16): apparatus is bench equipment.
        entity.destructible = false
        entity.minable = false
        entity.operable = false
        local runtime = {
          unit_number = entity.unit_number,
          direction = port_config.direction,
          item = port_config.material.item,
          system = port_config.system,
          prev_post_settlement_count = 0,
          supply = nil,
          totals = {
            withdrawal = 0, release = 0, delivery = 0,
            reverse_flow = 0, contamination = 0,
          },
        }
        if port_config.supply then
          runtime.supply = {
            mode = port_config.supply.mode,
            target = port_config.supply.target,
            active_phases = {},
            schedule = nil,
            external_pending = 0,
            external_capacity = nil, -- nil = unbounded
            supply_lost = 0,
          }
          for _, phase_id in ipairs(port_config.supply.active_phases or {}) do
            runtime.supply.active_phases[phase_id] = true
          end
          if port_config.supply.schedule then
            runtime.supply.schedule = schedules.new_constant(
              port_config.supply.schedule.quantity,
              port_config.supply.schedule.period_ticks)
          end
          if port_config.supply.external_buffer then
            if port_config.supply.external_buffer.kind == "finite" then
              runtime.supply.external_capacity = port_config.supply.external_buffer.quantity
            end
          end
          -- Explicit initial staging state (ADR 0003 §17), established at
          -- READY rather than trusting accidental save inventory.
          local initial_quantity = port_config.supply.initial_quantity or 0
          if initial_quantity > 0 then
            chest_inventory(entity).insert({ name = runtime.item, count = initial_quantity })
          end
        end
        runtime.prev_post_settlement_count = chest_inventory(entity).get_item_count(runtime.item)
        s.ports[port_id] = runtime
      end
    end
  end
  if #problems > 0 then return problems end
  return nil
end

-- Transient LuaEntity cache keyed by unit_number. Module locals reset on
-- save/load, so this rebuilds lazily and persistent state stays boring data.
local entity_cache = {}

function ports.entity_for(port_runtime)
  local cached = entity_cache[port_runtime.unit_number]
  if cached and cached.valid then return cached end
  for _, surface in pairs(game.surfaces) do
    local found = surface.find_entities_filtered({ name = { "fisl-source-port", "fisl-sink-port" } })
    for _, entity in ipairs(found) do
      if entity.unit_number == port_runtime.unit_number then
        entity_cache[port_runtime.unit_number] = entity
        return entity
      end
    end
  end
  return nil
end

--- Settle the completed interval [T-1, T) for every port (pipeline step 2).
--- Returns per-flow admission/completion quantities in raw item units.
function ports.settle_interval(experiment_tick, phase_id)
  local s = state.get()
  local results = { withdrawals = {}, deliveries = {}, lost_port = nil }
  for port_id, port in pairs(s.ports) do
    local entity = ports.entity_for(port)
    if entity == nil or not entity.valid then
      results.lost_port = port_id
      telemetry.emit({
        type = "port_binding_lost", port = port_id,
        experiment_tick = experiment_tick,
      })
    else
      local inventory = chest_inventory(entity)
      local current = inventory.get_item_count(port.item)
      if port.direction == "source" then
        local delta = port.prev_post_settlement_count - current
        if delta > 0 then
          port.totals.withdrawal = port.totals.withdrawal + delta
          results.withdrawals[port_id] = delta
          telemetry.emit({
            type = "source_withdrawal", port = port_id, quantity = delta,
            interval_start_tick = experiment_tick - 1, interval_end_tick = experiment_tick,
            phase = phase_id, method = "net_inventory_delta",
          })
        elseif delta < 0 then
          -- More tracked material than we left: reverse flow (ADR 0003 §8).
          port.totals.reverse_flow = port.totals.reverse_flow - delta
          telemetry.emit({
            type = "source_reverse_flow", port = port_id, quantity = -delta,
            interval_start_tick = experiment_tick - 1, interval_end_tick = experiment_tick,
            phase = phase_id,
          })
          ports.count_protocol_event("source_reverse_flow")
        end
        port.prev_post_settlement_count = current
      else -- sink
        if current > 0 then
          local removed = inventory.remove({ name = port.item, count = current })
          port.totals.delivery = port.totals.delivery + removed
          results.deliveries[port_id] = removed
          telemetry.emit({
            type = "sink_delivery", port = port_id, quantity = removed,
            interval_start_tick = experiment_tick - 1, interval_end_tick = experiment_tick,
            phase = phase_id, method = "settlement_removal",
          })
        end
      end
      -- Contamination check (ADR 0003 §18): any other item in the endpoint.
      local total_items = inventory.get_item_count()
      local tracked = inventory.get_item_count(port.item)
      if total_items > tracked then
        port.totals.contamination = total_items - tracked
        telemetry.emit({
          type = "port_contamination", port = port_id,
          quantity = total_items - tracked, experiment_tick = experiment_tick,
        })
        ports.count_protocol_event("port_contamination")
      end
    end
  end
  return results
end

--- Apply FISL-controlled apparatus mutations for the upcoming interval
--- [T, T+1) (pipeline steps 6-7): scheduled release / replenishment.
function ports.prepare_interval(experiment_tick, phase_id)
  local s = state.get()
  for port_id, port in pairs(s.ports) do
    local supply = port.supply
    if supply then
      local active = supply.active_phases[phase_id] == true
      local entity = ports.entity_for(port)
      if entity and entity.valid then
        local inventory = chest_inventory(entity)
        if supply.mode == "replenish" and active then
          local current = inventory.get_item_count(port.item)
          if current < supply.target then
            local inserted = inventory.insert({ name = port.item, count = supply.target - current })
            if inserted > 0 then
              telemetry.emit({
                type = "source_release", port = port_id, quantity = inserted,
                experiment_tick = experiment_tick, method = "fisl_controlled_transaction",
              })
              port.totals.release = port.totals.release + inserted
            end
          end
        elseif supply.mode == "scheduled" then
          local newly_available = 0
          if active and supply.schedule then
            newly_available = schedules.advance(supply.schedule)
          end
          -- stage as much as possible: external pending first (FIFO), then new
          local to_stage = supply.external_pending + newly_available
          local inserted = 0
          if to_stage > 0 then
            inserted = inventory.insert({ name = port.item, count = to_stage })
          end
          local blocked = to_stage - inserted
          if supply.external_capacity ~= nil and blocked > supply.external_capacity then
            local lost = blocked - supply.external_capacity
            supply.supply_lost = supply.supply_lost + lost
            blocked = supply.external_capacity
            telemetry.emit({
              type = "source_supply_lost", port = port_id, quantity = lost,
              experiment_tick = experiment_tick,
            })
          end
          supply.external_pending = blocked
          if inserted > 0 then
            telemetry.emit({
              type = "source_release", port = port_id, quantity = inserted,
              experiment_tick = experiment_tick, method = "fisl_controlled_transaction",
            })
            port.totals.release = port.totals.release + inserted
          end
        end
        -- settlement baseline for the next interval's net-delta measurement
        port.prev_post_settlement_count = inventory.get_item_count(port.item)
      end
    end
  end
end

function ports.count_protocol_event(kind)
  local s = state.get()
  s.validity.protocol_events[kind] = (s.validity.protocol_events[kind] or 0) + 1
end

return ports
