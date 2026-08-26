-- FISL core runtime wiring.
--
-- Single-writer model (ADR 0004 §3): event handlers below only queue raw
-- notifications or handle GUI/lifecycle edges; all authoritative experiment
-- state mutation happens inside experiment.checkpoint on_tick.

local state = require("fisl.state")
local lifecycle = require("fisl.lifecycle")
local experiment = require("fisl.experiment")
local ports = require("fisl.ports")
local gui = require("fisl.gui")

script.on_init(function()
  state.reset()
end)

-- Narrow versioned remote interface (ADR 0015 §4). Invoked by the controller
-- through RCON as: /sc rcon.print(remote.call("fisl", "<fn>", ...))
remote.add_interface("fisl", {
  get_protocol_version = lifecycle.get_protocol_version,
  begin_configuration = lifecycle.begin_configuration,
  append_configuration = lifecycle.append_configuration,
  commit_configuration = lifecycle.commit_configuration,
  request_start = lifecycle.request_start,
  request_abort = lifecycle.request_abort,
  get_status = lifecycle.get_status,
  get_summary = lifecycle.get_summary,
  request_final_save = lifecycle.request_final_save,
})

script.on_event(defines.events.on_tick, function()
  local s = state.get()
  if s.config and (s.lifecycle == "RUNNING" or s.run.pending_start) then
    experiment.checkpoint(s.config)
  end
  -- UI refresh cadence is presentation only (ADR 0011 §15): once per second.
  if s.config and game.tick % 60 == 0 then
    gui.refresh_all()
  end
end)

-- Sensor handlers: capture minimal raw notifications for the coordinator
-- (ADR 0004 §3). The coordinator drains these at the next checkpoint
-- boundary; entity-set membership additions consume `entity` (a LuaEntity
-- reference that never reaches telemetry — it is stripped at drain).
local function queue_entity_notification(kind, event)
  local s = state.get()
  if s.lifecycle ~= "RUNNING" then return end
  local entity = event.entity or event.created_entity
  if entity == nil or not entity.valid then return end
  s.events.raw_queue[#s.events.raw_queue + 1] = {
    type = kind,
    factorio_event_tick = event.tick,
    entity_name = entity.name,
    entity_type = entity.type,
    unit_number = entity.unit_number,
    position = { x = entity.position.x, y = entity.position.y },
    surface = entity.surface and entity.surface.name or nil,
    entity = kind == "entity_created" and entity or nil,
  }
end

script.on_event(defines.events.on_built_entity, function(event)
  queue_entity_notification("entity_created", event)
end)
script.on_event(defines.events.on_robot_built_entity, function(event)
  queue_entity_notification("entity_created", event)
end)
script.on_event(defines.events.script_raised_built, function(event)
  queue_entity_notification("entity_created", event)
end)
script.on_event(defines.events.script_raised_revive, function(event)
  queue_entity_notification("entity_created", event)
end)
script.on_event(defines.events.on_player_mined_entity, function(event)
  queue_entity_notification("entity_removed", event)
end)
script.on_event(defines.events.on_robot_mined_entity, function(event)
  queue_entity_notification("entity_removed", event)
end)
script.on_event(defines.events.on_entity_died, function(event)
  queue_entity_notification("entity_removed", event)
end)
script.on_event(defines.events.script_raised_destroy, function(event)
  queue_entity_notification("entity_removed", event)
end)

script.on_event(defines.events.on_player_joined_game, function(event)
  local player = game.get_player(event.player_index)
  if player then gui.rebuild(player) end
end)

-- ADR 0018 §3: unexpected required-learner disconnect during RUNNING aborts.
script.on_event(defines.events.on_player_left_game, function(event)
  local s = state.get()
  if s.config == nil or s.lifecycle ~= "RUNNING" then return end
  local profile = s.config.run.run_profile
  if profile.required_learner_connection then
    local connected = 0
    for _, player in pairs(game.players) do
      if player.connected then connected = connected + 1 end
    end
    if connected == 0 then
      ports.count_protocol_event("learner_disconnected")
      experiment.abort(s.config, "learner_disconnected")
      gui.refresh_all()
    end
  end
end)

script.on_event(defines.events.on_gui_click, function(event)
  if event.element and event.element.valid and event.element.name == "fisl_start_button" then
    lifecycle.request_start()
    local player = game.get_player(event.player_index)
    if player then gui.rebuild(player) end
  end
end)
