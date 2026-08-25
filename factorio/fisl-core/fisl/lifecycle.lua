-- Run lifecycle + controller protocol (ADR 0015, PRD §13-§14).
--
-- The remote interface is narrow and versioned. Configuration arrives as
-- base64(deflate(JSON)) chunks; commit verifies chunk count and a CRC-32 of
-- the decoded JSON text against the values declared at begin (ADR 0015 §6).

local util = require("fisl.util")
local state = require("fisl.state")
local telemetry = require("fisl.telemetry")
local ports = require("fisl.ports")
local ledger = require("fisl.ledger")
local census = require("fisl.census")
local experiment = require("fisl.experiment")

local lifecycle = {}

local PROTOCOL_VERSION = 1

function lifecycle.get_protocol_version()
  return tostring(PROTOCOL_VERSION)
end

function lifecycle.begin_configuration(run_id, crc, total_chunks)
  state.reset()
  local s = state.get()
  s.protocol.transfer = {
    run_id = run_id,
    crc32 = tonumber(crc),
    total_chunks = tonumber(total_chunks),
    chunks = {},
    received = 0,
  }
  return util.json_encode({ ok = true, run_id = run_id })
end

function lifecycle.append_configuration(index, payload)
  local s = state.get()
  local transfer = s.protocol.transfer
  if transfer == nil then
    return util.json_encode({ ok = false, error = "no transfer in progress" })
  end
  index = tonumber(index)
  if transfer.chunks[index] ~= nil then
    return util.json_encode({ ok = false, error = "duplicate chunk " .. index })
  end
  transfer.chunks[index] = payload
  transfer.received = transfer.received + 1
  return util.json_encode({ ok = true, received = transfer.received })
end

function lifecycle.commit_configuration()
  local s = state.get()
  local transfer = s.protocol.transfer
  if transfer == nil then
    return util.json_encode({ ok = false, error = "no transfer in progress" })
  end
  if transfer.received ~= transfer.total_chunks then
    return util.json_encode({
      ok = false,
      error = string.format("received %d of %d chunks", transfer.received, transfer.total_chunks),
    })
  end
  local encoded_parts = {}
  for index = 1, transfer.total_chunks do
    local chunk = transfer.chunks[index]
    if chunk == nil then
      return util.json_encode({ ok = false, error = "missing chunk " .. index })
    end
    encoded_parts[index] = chunk
  end
  local decode_ok, decoded = pcall(util.decode_payload, table.concat(encoded_parts))
  if not decode_ok or decoded == nil then
    return util.json_encode({ ok = false, error = "payload decode failed" })
  end
  local crc = util.crc32(decoded)
  if crc ~= transfer.crc32 then
    return util.json_encode({
      ok = false,
      error = string.format("crc mismatch: expected %d got %d", transfer.crc32, crc),
    })
  end
  local parse_ok, document = pcall(util.json_decode, decoded)
  if not parse_ok or document == nil
      or document.resolved_scenario == nil or document.run_configuration == nil then
    return util.json_encode({ ok = false, error = "malformed configuration document" })
  end
  if document.resolved_scenario.protocol_version ~= PROTOCOL_VERSION then
    return util.json_encode({
      ok = false,
      error = "protocol version mismatch: runtime=" .. PROTOCOL_VERSION,
    })
  end
  s.config = {
    run = document.run_configuration,
    resolved = document.resolved_scenario,
  }
  s.protocol.transfer = nil
  s.run.run_id = document.run_configuration.run_id

  local problems = lifecycle.validate_ready()
  if problems then
    s.lifecycle = "INITIALIZING"
    return util.json_encode({ ok = false, error = "READY validation failed", problems = problems })
  end
  return util.json_encode({ ok = true, lifecycle = s.lifecycle, run_id = s.run.run_id })
end

--- READY validation (FR-LIFE-001): bindings, prototypes, initial census.
function lifecycle.validate_ready()
  local s = state.get()
  local config = s.config
  local problems = {}

  -- Required prototypes: every flow-basis material must exist as an item.
  for _, flow in pairs(config.resolved.flows) do
    for item in pairs(flow.basis.materials) do
      if prototypes.item[item] == nil then
        problems[#problems + 1] = "missing item prototype " .. item
      end
    end
  end
  -- Zones must resolve to real surfaces.
  for zone_id, zone in pairs(config.resolved.zones) do
    if game.surfaces[zone.surface] == nil then
      problems[#problems + 1] = "zone " .. zone_id .. ": unknown surface " .. zone.surface
    end
  end
  if #problems > 0 then return problems end

  local binding_problems = ports.bind_all(config)
  if binding_problems then return binding_problems end

  telemetry.init(s.run.run_id)
  ledger.init(config)
  census.init(config)
  experiment.init_accumulators(config)

  -- Initial census establishes and validates initial WIP (ADR 0017 §4).
  for flow_id, led in pairs(s.ledgers) do
    local decomposition, total = census.take(config, flow_id, true)
    if decomposition == nil then
      problems[#problems + 1] = "initial census failed for flow " .. flow_id
    elseif total ~= 0 then
      -- Canonical baselines start empty; a nonzero start needs explicit
      -- scenario support which the POC schema does not yet model.
      problems[#problems + 1] = string.format(
        "flow %s: baseline contains %d tracked work units; canonical baselines must start at WIP=0",
        flow_id, total)
    else
      led.initial_wip = 0
      telemetry.emit({
        type = "initial_census", flow = flow_id, wip = 0,
        decomposition = decomposition, method = "physical_census",
      })
    end
  end
  if #problems > 0 then return problems end

  s.lifecycle = "READY"
  telemetry.emit({ type = "lifecycle", lifecycle = "READY" })
  telemetry.flush(false)
  return nil
end

function lifecycle.request_start()
  local s = state.get()
  if s.lifecycle ~= "READY" then
    return util.json_encode({ ok = false, error = "not READY (lifecycle=" .. s.lifecycle .. ")" })
  end
  s.run.pending_start = true
  -- The coordinator assigns experiment_tick 0 at the next executed tick
  -- boundary (ADR 0001 §9, ADR 0015 §7).
  return util.json_encode({ ok = true, pending_start = true })
end

function lifecycle.request_abort(reason)
  local s = state.get()
  if s.config and (s.lifecycle == "RUNNING" or s.lifecycle == "READY") then
    experiment.abort(s.config, reason or "controller_abort")
    return util.json_encode({ ok = true, lifecycle = s.lifecycle })
  end
  return util.json_encode({ ok = false, error = "nothing to abort" })
end

function lifecycle.get_status()
  local s = state.get()
  local status = {
    lifecycle = s.lifecycle,
    run_id = s.run.run_id,
    abort_reason = s.abort_reason,
    map_tick = game.tick,
  }
  if s.run.experiment_start_map_tick and s.lifecycle == "RUNNING" then
    status.experiment_tick = game.tick - s.run.experiment_start_map_tick
  end
  if s.config and (s.lifecycle == "RUNNING" or s.lifecycle == "COMPLETED" or s.lifecycle == "ABORTED") then
    status.ledgers = {}
    for flow_id in pairs(s.ledgers) do
      status.ledgers[flow_id] = ledger.snapshot(flow_id)
    end
  end
  return util.json_encode(status)
end

function lifecycle.get_summary()
  local s = state.get()
  if s.config == nil then
    return util.json_encode({ ok = false, error = "no configuration" })
  end
  return util.json_encode({ ok = true, summary = experiment.summary(s.config) })
end

function lifecycle.request_final_save(name)
  if game.server_save then
    game.server_save(name)
    return util.json_encode({ ok = true })
  end
  return util.json_encode({ ok = false, error = "server_save unavailable" })
end

return lifecycle
