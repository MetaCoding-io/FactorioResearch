-- Minimal learner GUI (PRD §22): READY/Start panel, RUNNING status with
-- learner_live metrics only, COMPLETED panel with learner_post_run values.
-- The GUI consumes authoritative FISL state; it never re-queries Factorio
-- with its own measurement logic (ADR 0004 §20, ADR 0011 §15).

local state = require("fisl.state")
local ledger = require("fisl.ledger")

local gui = {}

local FRAME = "fisl_panel"

local function live_metric_ids(config)
  local visible = {}
  for _, metric_id in ipairs(config.resolved.visibility.learner_live.metrics or {}) do
    visible[#visible + 1] = metric_id
  end
  return visible
end

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
  if s.lifecycle == "RUNNING" then
    for _, metric_id in ipairs(live_metric_ids(config)) do
      local value = metric_display_value(config, metric_id)
      if value then
        metrics_flow.add({ type = "label", caption = metric_id .. ": " .. value })
      end
    end
  elseif s.lifecycle == "COMPLETED" then
    metrics_flow.add({
      type = "label",
      caption = "Experiment complete. Post-run report: fisl report runs/" .. (s.run.run_id or "?"),
    })
    for flow_id in pairs(state.get().ledgers) do
      local snapshot = ledger.snapshot(flow_id)
      metrics_flow.add({
        type = "label",
        caption = string.format(
          "%s: admitted %d, completed %d, final WIP %d",
          flow_id, snapshot.admissions, snapshot.completions, snapshot.wip),
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
