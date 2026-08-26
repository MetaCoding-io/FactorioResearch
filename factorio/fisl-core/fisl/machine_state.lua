-- Runtime production-state adapter for crafting machines (ADR 0007).
--
-- Feeds the pure classifier (fisl/classify.lua) with per-tick point samples
-- taken at canonical checkpoint boundaries and emits run-length-encoded
-- classified spans to telemetry. Python recomputes authoritative state-time
-- aggregations from the spans; the in-run accumulators exist only for the
-- summary cross-check (revision 8/9 division of labor).
--
-- Membership is resolved ONCE at READY (static membership). This is an
-- interim simplification of ADR 0016 dynamic entity sets, tracked as GitHub
-- issue #8: entities placed/removed mid-run are not picked up. Each
-- membership record declares `membership_resolution = "static_at_ready"` so
-- run data is honest about it.

local state = require("fisl.state")
local telemetry = require("fisl.telemetry")
local classify = require("fisl.classify")

local machine_state = {}

machine_state.ADAPTER = "crafting_machine"

-- defines.entity_status value -> name, resolved deterministically (sorted
-- names, first wins) because pairs() order is unspecified.
local STATUS_NAME = nil

local function status_name_table()
  if STATUS_NAME then return STATUS_NAME end
  local names = {}
  for name in pairs(defines.entity_status) do names[#names + 1] = name end
  table.sort(names)
  STATUS_NAME = {}
  for _, name in ipairs(names) do
    local value = defines.entity_status[name]
    if STATUS_NAME[value] == nil then STATUS_NAME[value] = name end
  end
  return STATUS_NAME
end

-- Entity families the crafting_machine adapter supports (ADR 0007 §3). Any
-- other family in the selector is a READY failure, never silently sampled.
local SUPPORTED_TYPES = {
  ["assembling-machine"] = true,
  ["furnace"] = true,
}

local function is_port_apparatus(s, entity)
  if entity.unit_number == nil then return true end
  for _, port in pairs(s.ports) do
    if port.unit_number == entity.unit_number then return true end
  end
  return false
end

--- Resolve static membership for every production_state metric and emit the
--- roster. Returns a list of problems (or nil) in READY-validation style.
function machine_state.init(config)
  local s = state.get()
  s.machine_state = {}
  local problems = {}
  for metric_id, metric in pairs(config.resolved.metrics) do
    if metric.type == "production_state" then
      local selector = config.resolved.entity_sets[metric.entities]
      if selector == nil then
        problems[#problems + 1] = "metrics." .. metric_id .. ": unknown entity_set " .. tostring(metric.entities)
      else
        local zone = config.resolved.zones[selector.zone]
        local surface = game.surfaces[zone.surface]
        local found = surface.find_entities_filtered({
          area = {
            { zone.area.left_top[1], zone.area.left_top[2] },
            { zone.area.right_bottom[1], zone.area.right_bottom[2] },
          },
          type = selector.types,
        })
        local machines, order = {}, {}
        for _, entity in ipairs(found) do
          local keep = not is_port_apparatus(s, entity)
          if keep and selector.prototypes and #selector.prototypes > 0 then
            keep = false
            for _, name in ipairs(selector.prototypes) do
              if entity.name == name then keep = true end
            end
          end
          if keep and not SUPPORTED_TYPES[entity.type] then
            problems[#problems + 1] = "metrics." .. metric_id .. ": entity type "
              .. entity.type .. " is not supported by the crafting_machine adapter"
            keep = false
          end
          if keep then
            machines[entity.unit_number] = {
              unit_number = entity.unit_number,
              prototype = entity.name,
              position = { x = entity.position.x, y = entity.position.y },
              prev = nil,          -- last point sample {tick, recipe, ...}
              span = nil,          -- open run-length span
              state_ticks = {},    -- headline -> classified interval count
              coverage_missing_ticks = 0,
            }
            order[#order + 1] = entity.unit_number
          end
        end
        table.sort(order)
        if #order == 0 then
          problems[#problems + 1] = "metrics." .. metric_id
            .. ": entity_set " .. metric.entities .. " matched no machines at READY"
        else
          s.machine_state[metric_id] = {
            adapter = machine_state.ADAPTER,
            classifier_version = classify.CLASSIFIER_VERSION,
            entity_set = metric.entities,
            machines = machines,
            order = order,
            last_classified_tick = nil,
          }
          local roster = {}
          for index, unit_number in ipairs(order) do
            local machine = machines[unit_number]
            roster[index] = {
              unit_number = machine.unit_number,
              prototype = machine.prototype,
              position = machine.position,
            }
          end
          telemetry.emit({
            type = "machine_state_membership",
            metric = metric_id,
            entity_set = metric.entities,
            adapter = machine_state.ADAPTER,
            classifier_version = classify.CLASSIFIER_VERSION,
            membership_resolution = "static_at_ready",
            machines = roster,
          })
        end
      end
    end
  end
  if #problems > 0 then return problems end
  return nil
end

--- Point sample of one machine's process state (ADR 0007 §5). Returns nil
--- when the entity is gone/invalid — classified as missing coverage, never
--- as an idle state (§24).
local function take_sample(unit_number)
  local entity = game.get_entity_by_unit_number(unit_number)
  if entity == nil or not entity.valid then return nil, nil end
  local recipe = entity.get_recipe()
  local sample = {
    recipe = recipe and recipe.name or nil,
    is_crafting = entity.is_crafting(),
    crafting_progress = entity.crafting_progress,
    products_finished = entity.products_finished,
  }
  return sample, status_name_table()[entity.status]
end

local function close_span(metric_id, machine, end_tick)
  local span = machine.span
  if span == nil then return end
  telemetry.emit({
    type = "machine_state_span",
    metric = metric_id,
    unit_number = machine.unit_number,
    from_tick = span.from_tick,
    to_tick = end_tick,               -- half-open [from_tick, to_tick)
    headline = span.headline,
    cause = span.cause,
    raw_status = span.raw_status,
    mapped = span.mapped,
  })
  machine.span = nil
end

local function record_interval(metric_id, machine, interval_start, record)
  -- accumulate (cross-check only; Python owns the authoritative aggregation)
  if record.headline == "coverage_missing" then
    machine.coverage_missing_ticks = machine.coverage_missing_ticks + 1
  else
    machine.state_ticks[record.headline] = (machine.state_ticks[record.headline] or 0) + 1
  end
  -- run-length encoding on (headline, cause, raw_status)
  local span = machine.span
  if span ~= nil
      and span.headline == record.headline
      and span.cause == record.cause
      and span.raw_status == record.raw_status then
    return
  end
  close_span(metric_id, machine, interval_start)
  machine.span = {
    from_tick = interval_start,
    headline = record.headline,
    cause = record.cause,
    raw_status = record.raw_status,
    mapped = record.mapped,
  }
end

--- Canonical checkpoint hook. At boundary T (experiment_tick), samples every
--- measured machine; for T >= 1 classifies the interval [T-1, T) from the
--- adjacent samples. The interval's condition/cause comes from the raw
--- status observed at the END boundary T (the status after the interval's
--- ticks executed reflects what constrained them); the raw point sample is
--- preserved inside the span either way (§1).
function machine_state.checkpoint(config, experiment_tick)
  local s = state.get()
  if s.machine_state == nil then return end
  for metric_id, tracker in pairs(s.machine_state) do
    for _, unit_number in ipairs(tracker.order) do
      local machine = tracker.machines[unit_number]
      local sample, raw_status = take_sample(unit_number)
      if experiment_tick > 0 then
        local record = classify.interval(machine.prev, sample, raw_status)
        record_interval(metric_id, machine, experiment_tick - 1, record)
      end
      machine.prev = sample
    end
    tracker.last_classified_tick = experiment_tick
  end
end

--- Close and emit every open span at final boundary `end_tick` (completion:
--- total duration). With end_tick == nil (abort), spans close at the last
--- classified boundary — intervals never observed are not invented.
function machine_state.flush_spans(end_tick)
  local s = state.get()
  if s.machine_state == nil then return end
  for metric_id, tracker in pairs(s.machine_state) do
    local boundary = end_tick or tracker.last_classified_tick
    if boundary ~= nil then
      for _, unit_number in ipairs(tracker.order) do
        close_span(metric_id, tracker.machines[unit_number], boundary)
      end
    end
  end
end

--- Summary contribution: pooled machine-tick counts per headline plus
--- coverage, per metric (cross-check against the Python recomputation).
function machine_state.summary()
  local s = state.get()
  if s.machine_state == nil then return nil end
  local out = {}
  for metric_id, tracker in pairs(s.machine_state) do
    local pooled, coverage_missing = {}, 0
    for _, unit_number in ipairs(tracker.order) do
      local machine = tracker.machines[unit_number]
      for headline, ticks in pairs(machine.state_ticks) do
        pooled[headline] = (pooled[headline] or 0) + ticks
      end
      coverage_missing = coverage_missing + machine.coverage_missing_ticks
    end
    out[metric_id] = {
      adapter = tracker.adapter,
      classifier_version = tracker.classifier_version,
      entity_set = tracker.entity_set,
      membership_resolution = "static_at_ready",
      machine_count = #tracker.order,
      pooled_state_ticks = pooled,
      coverage_missing_ticks = coverage_missing,
      last_classified_tick = tracker.last_classified_tick,
    }
  end
  return out
end

return machine_state
