-- Persistent state layout ("persistent state should be boring data",
-- ARCHITECTURE.md §17 / ADR 0014 §10). Everything in storage.fisl is plain
-- reconstructible data: strings, numbers, booleans, tables, unit_numbers.

local state = {}

function state.reset()
  storage.fisl = {
    lifecycle = "INITIALIZING",   -- INITIALIZING|READY|RUNNING|COMPLETED|ABORTED
    abort_reason = nil,
    protocol = {
      -- chunked config transfer assembly area (ADR 0015 §6)
      transfer = nil,             -- {run_id, crc32, total_chunks, byte_len, chunks={}}
    },
    config = nil,                 -- decoded RunConfiguration+ResolvedScenario document
    run = {
      run_id = nil,
      experiment_start_map_tick = nil,  -- map tick of experiment_tick 0
      pending_start = false,
      current_phase_index = nil,
      completed_map_tick = nil,
    },
    ports = {},                   -- port_id -> runtime port state
    ledgers = {},                 -- flow_id -> conservation ledger state
    census = {},                  -- metric_id -> census validation state
    accumulators = {},            -- metric_id -> exact streaming accumulator
    telemetry = {
      sequence = 0,
      buffer = {},                -- pending encoded JSONL lines
      flush_every = 60,
      path = nil,
    },
    events = {
      raw_queue = {},             -- sensor notifications awaiting the coordinator
    },
    validity = {
      protocol_events = {},       -- summary counters by kind
      manual_carriage_seen = false,
    },
    gui = {},
  }
end

function state.get()
  if storage.fisl == nil then state.reset() end
  return storage.fisl
end

return state
