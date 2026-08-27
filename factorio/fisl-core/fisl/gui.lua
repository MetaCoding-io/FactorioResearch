-- Minimal learner GUI (PRD §22): READY/Start panel, RUNNING status with
-- learner_live metrics only, COMPLETED panel with learner_post_run values.
-- The GUI consumes authoritative FISL state; it never re-queries Factorio
-- with its own measurement logic (ADR 0004 §20, ADR 0011 §15).

local state = require("fisl.state")
local ledger = require("fisl.ledger")

local gui = {}

local FRAME = "fisl_panel"

local function metric_display_value(config, metric_id)
  local s = state.get()
  local metric = config.resolved.metrics[metric_id]
  if metric == nil then return nil end
  if metric.type == "current_value" then
    local source = config.resolved.metrics[metric.source]
    if source and source.type == "wip" then
      return string.format("%d %s", ledger.wip(source.flow), "work units")
    end
  elseif metric.type == "wip" then
    return string.format("%d work units", ledger.wip(metric.flow))
  end
  return nil
end

--- Final value of a learner_post_run metric from the exact in-run
--- accumulators, where one exists. Metrics the runtime cannot finalize
--- (state fractions, service, percentiles) return nil — they belong to the
--- authoritative post-run report, and the panel says so rather than
--- showing a provisional stand-in (ADR 0011 §6).
local function post_run_display_value(config, metric_id)
  local s = state.get()
  local metric = config.resolved.metrics[metric_id]
  if metric == nil then return nil end
  if metric.type == "current_value" or metric.type == "wip" then
    return metric_display_value(config, metric_id)
  end
  local acc = s.accumulators[metric_id]
  if metric.type == "aggregate" and acc and acc.type == "time_mean" and acc.ticks > 0 then
    return string.format("%.2f work units", acc.area / acc.ticks)
  end
  if metric.type == "throughput" and acc then
    local ticks = acc.window.end_tick - acc.window.start_tick
    return string.format("%.2f/min", acc.completed * 3600.0 / ticks)
  end
  if metric.type == "cycle_time" then
    local wip_acc = s.accumulators[metric.wip_metric]
    local th_acc = s.accumulators[metric.throughput_metric]
    if wip_acc and th_acc and th_acc.completed > 0 then
      return string.format("%.2f s", wip_acc.area / th_acc.completed / 60.0)
    end
  end
  return nil
end

local function format_objective_bound(unit, value)
  if unit == "fraction" then return string.format("%.0f%%", value * 100) end
  if unit == "per_minute" then return string.format("%.2f/min", value) end
  if unit == "seconds" then return string.format("%.0f s", value) end
  return string.format("%.2f", value)
end

--- Disclosed objective RULE captions (ADR 0011 §7: the target is its own
--- disclosure; final status comes from the authoritative post-run report,
--- never a provisional in-game verdict).
local function objective_rule_caption(config, objective_id)
  local objective = (config.resolved.objectives or {})[objective_id]
  if objective == nil then return nil end
  if objective.type == "requirement" then
    local parts = {}
    if objective.minimum ~= nil then
      parts[#parts + 1] = ">= " .. format_objective_bound(objective.unit, objective.minimum)
    end
    if objective.maximum ~= nil then
      parts[#parts + 1] = "<= " .. format_objective_bound(objective.unit, objective.maximum)
    end
    return string.format("Objective: keep %s %s", objective.metric, table.concat(parts, " and "))
  end
  return string.format("Objective: %s %s", objective.direction, objective.metric)
end

local function add_disclosed_objectives(config, audience, target_flow)
  local audience_visibility = config.resolved.visibility[audience] or {}
  for _, objective_id in ipairs(audience_visibility.objectives or {}) do
    local caption = objective_rule_caption(config, objective_id)
    if caption then
      target_flow.add({ type = "label", caption = caption })
    end
  end
end

function gui.rebuild(player)
  local s = state.get()
  local root = player.gui.left
  if root[FRAME] then root[FRAME].destroy() end
  if s.config == nil then return end
  local config = s.config
  local frame = root.add({ type = "frame", name = FRAME, direction = "vertical" })
  frame.add({
    type = "label", name = "title",
    caption = "FISL: " .. (config.resolved.scenario.title or config.resolved.scenario.id),
    style = "frame_title",
  })
  frame.add({ type = "label", name = "status", caption = "" })
  if s.lifecycle == "READY" and config.run.run_profile.mode == "interactive" then
    frame.add({
      type = "button", name = "fisl_start_button", caption = "Start Experiment",
      style = "confirm_button",
    })
  end
  frame.add({ type = "flow", name = "metrics", direction = "vertical" })
  gui.refresh(player)
end

function gui.refresh(player)
  local s = state.get()
  local frame = player.gui.left[FRAME]
  if frame == nil or s.config == nil then return end
  local config = s.config

  local status_text = "Status: " .. s.lifecycle
  if s.lifecycle == "RUNNING" and s.run.experiment_start_map_tick then
    local experiment_tick = game.tick - s.run.experiment_start_map_tick
    local phase_index = s.run.current_phase_index
    local phase = phase_index and config.resolved.experiment.phases[phase_index] or nil
    local total = config.resolved.experiment.total_duration_ticks
    status_text = string.format(
      "Phase: %s   %d:%02d / %d:%02d",
      phase and phase.id or "?",
      math.floor(experiment_tick / 3600), math.floor((experiment_tick % 3600) / 60),
      math.floor(total / 3600), math.floor((total % 3600) / 60))
  end
  frame.status.caption = status_text

  if frame.fisl_start_button and s.lifecycle ~= "READY" then
    frame.fisl_start_button.destroy()
  end

  local metrics_flow = frame.metrics
  metrics_flow.clear()
  if s.lifecycle == "READY" then
    add_disclosed_objectives(config, "learner_live", metrics_flow)
  elseif s.lifecycle == "RUNNING" then
    add_disclosed_objectives(config, "learner_live", metrics_flow)
    for _, metric_id in ipairs(config.resolved.visibility.learner_live.metrics or {}) do
      local value = metric_display_value(config, metric_id)
      if value then
        metrics_flow.add({ type = "label", caption = metric_id .. ": " .. value })
      end
    end
  elseif s.lifecycle == "COMPLETED" then
    -- Post-run disclosure is allowlist-driven (ADR 0011 §3): only metrics
    -- named in learner_post_run appear, and only those the runtime can
    -- finalize exactly; everything else defers to the authoritative report.
    metrics_flow.add({
      type = "label",
      caption = "Experiment complete. Full report: fisl report runs/" .. (s.run.run_id or "?"),
    })
    add_disclosed_objectives(config, "learner_post_run", metrics_flow)
    local deferred = {}
    for _, metric_id in ipairs(config.resolved.visibility.learner_post_run.metrics or {}) do
      local value = post_run_display_value(config, metric_id)
      if value then
        metrics_flow.add({ type = "label", caption = metric_id .. ": " .. value })
      else
        deferred[#deferred + 1] = metric_id
      end
    end
    if #deferred > 0 then
      metrics_flow.add({
        type = "label",
        caption = "In the report: " .. table.concat(deferred, ", "),
      })
    end
  elseif s.lifecycle == "ABORTED" then
    metrics_flow.add({ type = "label", caption = "Aborted: " .. (s.abort_reason or "unknown") })
  end
end

function gui.refresh_all()
  for _, player in pairs(game.players) do
    gui.refresh(player)
  end
end

function gui.rebuild_all()
  for _, player in pairs(game.players) do
    gui.rebuild(player)
  end
end

return gui
