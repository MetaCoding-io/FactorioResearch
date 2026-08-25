-- Authoritative telemetry stream (ADR 0004 §6-§7, ADR 0013 §14-§15,
-- POST_REVIEW_REVISIONS.md revision 9).
--
-- Records are buffered and flushed to script-output as JSON Lines in batches
-- (default every 60 ticks and at lifecycle boundaries); each record carries a
-- monotonic sequence number, tick semantics, and measurement method.

local util = require("fisl.util")
local state = require("fisl.state")

local telemetry = {}

function telemetry.init(run_id)
  local s = state.get()
  s.telemetry.sequence = 0
  s.telemetry.buffer = {}
  s.telemetry.path = "fisl/" .. run_id .. "/telemetry.jsonl"
  -- truncate/claim the stream file with a header record
  telemetry.emit({ type = "stream_header", run_id = run_id, schema = "fisl-telemetry/1" })
  telemetry.flush(true)
end

--- Append one record. `record.type` is required; tick fields are supplied by
--- callers because temporal semantics differ by record class (ADR 0004 §5).
function telemetry.emit(record)
  local s = state.get()
  s.telemetry.sequence = s.telemetry.sequence + 1
  record.seq = s.telemetry.sequence
  record.map_tick = game and game.tick or nil
  s.telemetry.buffer[#s.telemetry.buffer + 1] = util.json_encode(record)
end

function telemetry.flush(first)
  local s = state.get()
  if #s.telemetry.buffer == 0 or s.telemetry.path == nil then return end
  local text = table.concat(s.telemetry.buffer, "\n") .. "\n"
  util.write_file(s.telemetry.path, text, not first)
  s.telemetry.buffer = {}
end

function telemetry.maybe_flush(experiment_tick)
  local s = state.get()
  if experiment_tick % s.telemetry.flush_every == 0 then
    telemetry.flush(false)
  end
end

return telemetry
