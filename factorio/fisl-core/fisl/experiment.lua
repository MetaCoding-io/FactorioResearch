-- The authoritative tick coordinator (ADR 0004 §9, PRD §15).
--
-- One on_tick checkpoint per executed map tick while a run is active. All
-- authoritative experiment state mutation happens here (single-writer model);
-- Factorio event handlers only queue raw notifications.

local state = require("fisl.state")
local telemetry = require("fisl.telemetry")
local ports = require("fisl.ports")
local ledger = require("fisl.ledger")
local census = require("fisl.census")
local machine_state = require("fisl.machine_state")

local experiment = {}

local function phase_for_tick(config, experiment_tick)
  for index, phase in ipairs(config.resolved.experiment.phases) do
    if experiment_tick >= phase.start_tick and experiment_tick < phase.end_tick then
      return index, phase
    end
  end
  return nil, nil
end

--- Initialize exact streaming accumulators for resolved metrics (ADR 0010,
--- revision 8: only what the runtime/live UI needs; Python recomputes
--- post-run results from telemetry).
function experiment.init_accumulators(config)
  local s = state.get()
  s.accumulators = {}
  for metric_id, metric in pairs(config.resolved.metrics) do
    if metric.type == "aggregate" then
      s.accumulators[metric_id] = {
        type = metric.aggregation, source = metric.source,
        window = metric.window, area = 0, ticks = 0,
        min = nil, max = nil,
      }
    elseif metric.type == "throughput" then
      s.accumulators[metric_id] = {
        type = "throughput", flow = metric.flow,
        boundary = metric.boundary or "completion",
        window = metric.window, completed = 0,
      }
    end
  end
end

local function source_flow(config, source_metric_id)
  local metric = config.resolved.metrics[source_metric_id]
  return metric and metric.flow or nil
end

local function accumulate_point_state(config, experiment_tick)
  local s = state.get()
  for metric_id, acc in pairs(s.accumulators) do
    if acc.type ~= "throughput" then
      local window = acc.window
      if experiment_tick >= window.start_tick and experiment_tick < window.end_tick then
        local flow = source_flow(config, acc.source)
        if flow then
          local value = ledger.wip(flow)
          acc.area = acc.area + value
          acc.ticks = acc.ticks + 1
          if acc.min == nil or value < acc.min then acc.min = value end
          if acc.max == nil or value > acc.max then acc.max = value end
        end
      end
    end
  end
end

local function accumulate_interval(config, settlement, interval_start_tick)
  local s = state.get()
  for _, acc in pairs(s.accumulators) do
    if acc.type == "throughput" then
      local window = acc.window
      if interval_start_tick >= window.start_tick and interval_start_tick < window.end_tick then
        local flow = config.resolved.flows[acc.flow]
        local quantities, boundary_ports
        if acc.boundary == "entry" then
          quantities, boundary_ports = settlement.withdrawals, flow.entry_ports
        else
          quantities, boundary_ports = settlement.deliveries, flow.completion_ports
        end
        for port_id, quantity in pairs(quantities) do
          for _, boundary_port in ipairs(boundary_ports) do
            if port_id == boundary_port then
              local item = s.ports[port_id].item
              local coefficient = flow.basis.materials[item] or 0
              acc.completed = acc.completed + quantity * coefficient
            end
          end
        end
      end
    end
  end
end

function experiment.summary(config)
  local s = state.get()
  local metrics = {}
  for metric_id, acc in pairs(s.accumulators) do
    if acc.type == "throughput" then
      metrics[metric_id] = {
        type = "throughput", flow = acc.flow, window = acc.window,
        completed_quantity = acc.completed,
        window_ticks = acc.window.end_tick - acc.window.start_tick,
        method = acc.boundary == "entry" and "entry_source_withdrawal" or "completion_sink_delivery",
      }
    elseif acc.type == "time_mean" or acc.type == "time_integral" then
      metrics[metric_id] = {
        type = "aggregate", aggregation = acc.type, window = acc.window,
        area = acc.area, ticks = acc.ticks, min = acc.min, max = acc.max,
      }
    elseif acc.type == "min" or acc.type == "max" then
      metrics[metric_id] = {
        type = "aggregate", aggregation = acc.type, window = acc.window,
        min = acc.min, max = acc.max,
      }
    end
  end
  local ledgers = {}
  for flow_id in pairs(s.ledgers) do
    ledgers[flow_id] = ledger.snapshot(flow_id)
  end
  local census_state = {}
  for metric_id, entry in pairs(s.census) do
    census_state[metric_id] = {
      last_good_tick = entry.last_good_tick,
      discrepancy_intervals = entry.discrepancy_intervals,
      coverage_incomplete_count = entry.coverage_incomplete_count,
    }
  end
  return {
    metrics = metrics,
    ledgers = ledgers,
    census = census_state,
    machine_state = machine_state.summary(),
    demand = ports.demand_summary(),
    protocol_events = s.validity.protocol_events,
    manual_carriage_seen = s.validity.manual_carriage_seen,
  }
end

local function finalize(config, experiment_tick)
  local s = state.get()
  -- Final machine-state boundary sample classifies the last interval
  -- [total-1, total) before spans are flushed (ADR 0007 §21).
  machine_state.checkpoint(config, experiment_tick)
  machine_state.flush_spans(experiment_tick)
  -- Terminal census + residual manual-carriage escalation (ADR 0017 §12).
  census.cross_check_forced(config, experiment_tick)
  for _, entry in pairs(s.census) do
    local decomposition = census.take(config, entry.flow, true)
    if decomposition and decomposition.player_inventory > 0 then
      telemetry.emit({
        type = "manual_carriage_residual",
        quantity = decomposition.player_inventory,
        experiment_tick = experiment_tick,
      })
      ports.count_protocol_event("manual_carriage_residual")
    end
  end
  telemetry.emit({
    type = "experiment_completed", experiment_tick = experiment_tick,
    summary = experiment.summary(config),
  })
  s.run.completed_map_tick = game.tick
  s.lifecycle = "COMPLETED"
  telemetry.flush(false)
  -- ADR 0001 §12 / ADR 0018 §5 recommend a terminal pause. Deliberately NOT
  -- implemented via game.tick_paused yet: if tick execution stops, RCON
  -- commands (tick-synchronized in multiplayer) may stall, deadlocking the
  -- controller's status polling. Post-completion drift cannot contaminate
  -- results because all metrics are windowed and settled above. RV-011
  -- evidence decides the final mechanism.
end

--- The per-tick checkpoint. Called from on_tick while lifecycle == RUNNING
--- (and once at start when a pending start is armed).
function experiment.checkpoint(config)
  local s = state.get()

  if s.run.pending_start then
    -- Clean tick boundary start (ADR 0001 §9): this tick is experiment_tick 0.
    s.run.pending_start = false
    s.run.experiment_start_map_tick = game.tick
    s.lifecycle = "RUNNING"
    telemetry.emit({ type = "experiment_started", experiment_tick = 0 })
    ports.stage_initial(0)
  end

  if s.lifecycle ~= "RUNNING" then return end

  local experiment_tick = game.tick - s.run.experiment_start_map_tick
  local total = config.resolved.experiment.total_duration_ticks

  -- Step 1: ingest queued sensor notifications. Entity-set membership
  -- changes take effect at THIS boundary (ADR 0016 §4: prepared for
  -- [T, T+1)); the LuaEntity reference rides only inside the queue and is
  -- stripped before the record goes to telemetry.
  if #s.events.raw_queue > 0 then
    for _, notification in ipairs(s.events.raw_queue) do
      machine_state.ingest(config, notification, experiment_tick)
      notification.entity = nil
      telemetry.emit(notification)
    end
    s.events.raw_queue = {}
  end

  local phase_index, phase
  -- Steps 2-3: settle the completed interval [T-1, T).
  if experiment_tick > 0 then
    local prior_phase_index, prior_phase = phase_for_tick(config, experiment_tick - 1)
    local settlement = ports.settle_interval(experiment_tick, prior_phase and prior_phase.id or nil)
    if settlement.lost_port then
      experiment.abort(config, "port_binding_lost:" .. settlement.lost_port)
      return
    end
    ledger.apply_settlement(settlement, experiment_tick, prior_phase and prior_phase.id or nil)
    accumulate_interval(config, settlement, experiment_tick - 1)
  end

  -- Step 4: final boundary => finalize instead of preparing another interval.
  if experiment_tick >= total then
    finalize(config, experiment_tick)
    return
  end

  -- Step 5: phase transition at boundary T.
  phase_index, phase = phase_for_tick(config, experiment_tick)
  if phase_index ~= s.run.current_phase_index then
    s.run.current_phase_index = phase_index
    telemetry.emit({
      type = "phase_transition", phase = phase.id, experiment_tick = experiment_tick,
    })
  end

  -- Steps 6-7: advance external processes / apparatus mutations for [T, T+1).
  ports.prepare_interval(experiment_tick, phase.id)

  -- Step 8: integrity checks are folded into settlement/census in the POC.

  -- Step 9: canonical prepared point-state samples + census cross-checks.
  census.cross_check(config, experiment_tick)
  accumulate_point_state(config, experiment_tick)
  machine_state.checkpoint(config, experiment_tick)

  -- Step 10: commit batch.
  telemetry.maybe_flush(experiment_tick)
end

function experiment.abort(config, reason)
  local s = state.get()
  -- Emit what was actually observed: spans close at the last classified
  -- boundary; nothing after it is invented (ADR 0007 §24).
  machine_state.flush_spans(nil)
  telemetry.emit({
    type = "experiment_aborted", reason = reason,
    experiment_tick = s.run.experiment_start_map_tick
      and (game.tick - s.run.experiment_start_map_tick) or nil,
    summary = experiment.summary(config),
  })
  s.lifecycle = "ABORTED"
  s.abort_reason = reason
  telemetry.flush(false)
end

return experiment
