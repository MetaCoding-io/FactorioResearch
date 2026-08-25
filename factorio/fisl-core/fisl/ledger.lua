-- Conservation-ledger WIP (ADR 0017 §1-§5, §18).
--
-- For each validated conserved flow:
--   WIP(T) = initial_WIP + admissions - completions - declared_losses
-- The ledger point state at boundary T is the prepared state for [T, T+1)
-- and is the authoritative total-WIP value; physical census (census.lua)
-- validates it at a coarse cadence and never rewrites it (ADR 0017 §8).

local state = require("fisl.state")
local telemetry = require("fisl.telemetry")

local ledger = {}

function ledger.init(config)
  local s = state.get()
  s.ledgers = {}
  for flow_id, flow in pairs(config.resolved.flows) do
    local coefficients = {}
    for item, coefficient in pairs(flow.basis.materials) do
      coefficients[item] = coefficient
    end
    local entry_ports, completion_ports, loss_ports = {}, {}, {}
    for _, p in ipairs(flow.entry_ports) do entry_ports[p] = true end
    for _, p in ipairs(flow.completion_ports) do completion_ports[p] = true end
    for _, p in ipairs(flow.loss_ports or {}) do loss_ports[p] = true end
    s.ledgers[flow_id] = {
      unit = flow.unit,
      coefficients = coefficients,
      entry_ports = entry_ports,
      completion_ports = completion_ports,
      loss_ports = loss_ports,
      initial_wip = 0,          -- established at READY census (ADR 0017 §4)
      admissions = 0,
      completions = 0,
      declared_losses = 0,
    }
  end
end

local function work_units(led, port_item, quantity)
  local coefficient = led.coefficients[port_item]
  if coefficient == nil then return 0 end
  return quantity * coefficient
end

--- Apply settled port interval results to every ledger (pipeline step 2/3).
function ledger.apply_settlement(settlement, experiment_tick, phase_id)
  local s = state.get()
  for flow_id, led in pairs(s.ledgers) do
    local admitted, completed = 0, 0
    for port_id, quantity in pairs(settlement.withdrawals) do
      if led.entry_ports[port_id] then
        admitted = admitted + work_units(led, s.ports[port_id].item, quantity)
      end
    end
    for port_id, quantity in pairs(settlement.deliveries) do
      if led.completion_ports[port_id] then
        completed = completed + work_units(led, s.ports[port_id].item, quantity)
      elseif led.loss_ports[port_id] then
        led.declared_losses = led.declared_losses + work_units(led, s.ports[port_id].item, quantity)
      end
    end
    if admitted > 0 then led.admissions = led.admissions + admitted end
    if completed > 0 then led.completions = led.completions + completed end
    if admitted > 0 or completed > 0 then
      telemetry.emit({
        type = "ledger_transaction", flow = flow_id,
        admitted = admitted, completed = completed,
        interval_start_tick = experiment_tick - 1, interval_end_tick = experiment_tick,
        phase = phase_id, method = "conservation_ledger",
      })
    end
  end
end

--- Authoritative WIP point state at the prepared boundary.
function ledger.wip(flow_id)
  local led = state.get().ledgers[flow_id]
  return led.initial_wip + led.admissions - led.completions - led.declared_losses
end

function ledger.snapshot(flow_id)
  local led = state.get().ledgers[flow_id]
  return {
    initial_wip = led.initial_wip,
    admissions = led.admissions,
    completions = led.completions,
    declared_losses = led.declared_losses,
    wip = ledger.wip(flow_id),
  }
end

return ledger
