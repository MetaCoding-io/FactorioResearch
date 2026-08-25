-- Exact rational schedule accumulation (ADR 0003 §12).
--
-- A constant schedule of `quantity` per `period_ticks` releases whole items
-- with an integer carry; no floating point is involved, so no drift.

local schedules = {}

function schedules.new_constant(quantity, period_ticks)
  return {
    kind = "constant",
    quantity = quantity,
    period_ticks = period_ticks,
    carry = 0,
  }
end

--- Advance one tick; returns the integer quantity released for the upcoming
--- interval.
function schedules.advance(sched)
  sched.carry = sched.carry + sched.quantity
  local released = math.floor(sched.carry / sched.period_ticks)
  sched.carry = sched.carry - released * sched.period_ticks
  return released
end

return schedules
