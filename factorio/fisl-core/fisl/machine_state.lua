-- Runtime production-state adapter for crafting machines (ADR 0007).
--
-- Feeds the pure classifier (fisl/classify.lua) with per-tick point samples
-- taken at canonical checkpoint boundaries and emits run-length-encoded
-- classified spans to telemetry. Python recomputes authoritative state-time
-- aggregations from the spans; the in-run accumulators exist only for the
-- summary cross-check (revision 8/9 division of labor).
--
-- Membership is DYNAMIC at canonical boundaries (ADR 0016, issue #8):
-- the READY scan seeds the roster (eligibility from tick 0), additions come
-- from the queued build-event notifications drained at checkpoint boundary
-- T (eligibility starts at T; no retroactive history, §6), and removals are
-- validity-driven — a member entity invalid at boundary T has its final
-- prepared interval [T-1, T) classified coverage_missing (it was prepared
-- at T-1), eligibility ends at T, and it leaves every later denominator.
-- Membership records declare `membership_resolution = "dynamic_boundary"`.
-- Known limitation: departure means the entity became invalid; an entity
-- that stops matching the selector while staying alive (not possible for
-- the v1 zone/type/prototype selectors — machines cannot move) is not
-- re-evaluated.

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

--- ADR 0016 §2/§9 selector predicate against one live entity (canonical
--- zone containment per ADR 0002: position >= left_top, < right_bottom).
local function matches_selector(s, config, selector, entity)
  local zone = config.resolved.zones[selector.zone]
  local position = entity.position
  local lt, rb = zone.area.left_top, zone.area.right_bottom
  if not (position.x >= lt[1] and position.x < rb[1]
      and position.y >= lt[2] and position.y < rb[2]) then
    return false
  end
  local type_ok = false
  for _, entity_type in ipairs(selector.types) do
    if entity.type == entity_type then type_ok = true end
  end
  if not type_ok then return false end
  if selector.prototypes and #selector.prototypes > 0 then
    local name_ok = false
    for _, name in ipairs(selector.prototypes) do
      if entity.name == name then name_ok = true end
    end
    if not name_ok then return false end
  end
  return not is_port_apparatus(s, entity)
end

local function new_member(entity, joined_tick)
  return {
    -- LuaEntity reference, deliberately held in storage (save/load-safe;
    -- RUNTIME_VALIDATION finding 5: per-tick unit-number lookup was
    -- unreliable on 2.0.77) — the reliable handle for sampling.
    entity = entity,
    unit_number = entity.unit_number,
    prototype = entity.name,
    position = { x = entity.position.x, y = entity.position.y },
    joined_tick = joined_tick,   -- eligibility interval start (ADR 0016 §5)
    left_tick = nil,             -- eligibility interval end; nil = still member
    prev = nil,                  -- last point sample
    span = nil,                  -- open run-length span
    state_ticks = {},            -- headline -> classified interval count
    coverage_missing_ticks = 0,
  }
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
          if matches_selector(s, config, selector, entity) then
            if SUPPORTED_TYPES[entity.type] then
              machines[entity.unit_number] = new_member(entity, 0)
              order[#order + 1] = entity.unit_number
            else
              problems[#problems + 1] = "metrics." .. metric_id .. ": entity type "
                .. entity.type .. " is not supported by the crafting_machine adapter"
            end
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
            membership_resolution = "dynamic_boundary",
            machines = roster,
          })
        end
      end
    end
  end
  if #problems > 0 then return problems end
  return nil
end

--- Consume one queued sensor notification at checkpoint boundary T
--- (ADR 0016 §3-§4): a built entity matching a selector becomes a member
--- at this boundary — eligibility [T, ...), first classified interval
--- [T, T+1). Removals are validity-driven in checkpoint(), not event-driven.
function machine_state.ingest(config, notification, boundary_tick)
  local s = state.get()
  if s.machine_state == nil then return end
  if notification.type ~= "entity_created" then return end
  local entity = notification.entity
  if entity == nil or not entity.valid then return end
  for metric_id, tracker in pairs(s.machine_state) do
    local selector = config.resolved.entity_sets[tracker.entity_set]
    if tracker.machines[entity.unit_number] == nil
        and matches_selector(s, config, selector, entity) then
      if SUPPORTED_TYPES[entity.type] then
        tracker.machines[entity.unit_number] = new_member(entity, boundary_tick)
        tracker.order[#tracker.order + 1] = entity.unit_number
        telemetry.emit({
          type = "machine_state_membership_change",
          metric = metric_id,
          change = "added",
          unit_number = entity.unit_number,
          prototype = entity.name,
          position = { x = entity.position.x, y = entity.position.y },
          boundary_tick = boundary_tick,
        })
      else
        -- ADR 0016 §11: an unsupported matching subject is visible coverage,
        -- never silently absent from the measurement.
        telemetry.emit({
          type = "machine_state_unsupported_member",
          metric = metric_id,
          unit_number = entity.unit_number,
          prototype = entity.name,
          entity_type = entity.type,
          boundary_tick = boundary_tick,
        })
      end
    end
  end
end

--- Point sample of one machine's process state (ADR 0007 §5). Returns nil
--- when the entity is gone/invalid — classified as missing coverage, never
--- as an idle state (§24).
local function take_sample(machine)
  local entity = machine.entity
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
      if machine.left_tick == nil then
        local sample, raw_status = take_sample(machine)
        if experiment_tick > machine.joined_tick then
          -- Only intervals inside the eligibility window are classified: a
          -- joiner's first classified interval is [joined, joined+1); its
          -- prior nonexistence is not unavailable/idle/coverage (ADR 0016 §6).
          local record = classify.interval(machine.prev, sample, raw_status)
          record_interval(metric_id, machine, experiment_tick - 1, record)
        end
        machine.prev = sample
        if sample == nil then
          -- Member entity is gone: eligibility ends at this boundary. The
          -- final prepared interval [T-1, T) above classified as
          -- coverage_missing (it WAS prepared at T-1); nothing after T
          -- belongs to this machine's denominator (ADR 0016 §5-§6).
          close_span(metric_id, machine, experiment_tick)
          machine.left_tick = experiment_tick
          machine.entity = nil
          telemetry.emit({
            type = "machine_state_membership_change",
            metric = metric_id,
            change = "removed",
            unit_number = machine.unit_number,
            prototype = machine.prototype,
            position = machine.position,
            boundary_tick = experiment_tick,
            eligible_from_tick = machine.joined_tick,
          })
        end
      end
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
    local eligible_ticks, current, total = 0, 0, 0
    for _, unit_number in ipairs(tracker.order) do
      local machine = tracker.machines[unit_number]
      total = total + 1
      if machine.left_tick == nil then current = current + 1 end
      for headline, ticks in pairs(machine.state_ticks) do
        pooled[headline] = (pooled[headline] or 0) + ticks
        eligible_ticks = eligible_ticks + ticks
      end
      coverage_missing = coverage_missing + machine.coverage_missing_ticks
      eligible_ticks = eligible_ticks + machine.coverage_missing_ticks
    end
    out[metric_id] = {
      adapter = tracker.adapter,
      classifier_version = tracker.classifier_version,
      entity_set = tracker.entity_set,
      membership_resolution = "dynamic_boundary",
      machine_count = current,
      members_total = total,
      eligible_machine_ticks = eligible_ticks,
      pooled_state_ticks = pooled,
      coverage_missing_ticks = coverage_missing,
      last_classified_tick = tracker.last_classified_tick,
    }
  end
  return out
end

return machine_state
