-- Pure production-state classification logic (ADR 0007). No Factorio
-- dependencies: this module is unit-tested outside the game (lupa) and the
-- runtime adapter (machine_state.lua) feeds it observations.
--
-- Version identity: bump when the mapping table or precedence changes;
-- recorded in run provenance (ADR 0007 §16).

local classify = {}

classify.CLASSIFIER_VERSION = "crafting_machine/1"

-- Raw Factorio status name -> constraint/cause (ADR 0007 classifier table).
-- Statuses not listed here are UNMAPPED and must surface as `unclassified`
-- coverage, never silently folded into a bucket (§15).
classify.CAUSE_BY_STATUS = {
  working = "none",
  item_ingredient_shortage = "input_shortage",
  fluid_ingredient_shortage = "input_shortage",
  no_ingredients = "input_shortage",
  full_output = "output_blocked",
  waiting_for_space_in_destination = "output_blocked",
  no_power = "energy_unavailable",
  low_power = "energy_limited",
  no_fuel = "energy_unavailable",
  frozen = "equipment_unavailable",
  broken = "equipment_unavailable",
  disabled_by_control_behavior = "disabled_control",
  disabled_by_script = "disabled_control",
  disabled = "disabled_control",
  no_recipe = "configuration",
  recipe_not_researched = "configuration",
}

classify.HEADLINES = {
  "productive", "starved", "blocked", "unavailable",
  "disabled", "idle_other", "unclassified",
}

--- Interval activity from adjacent canonical samples (ADR 0007 §7).
--- A sample is {recipe=?, is_crafting=?, crafting_progress=?, products_finished=?}.
--- Never a naive progress comparison: completion resets progress, so the
--- monotonic products_finished counter is consulted first (RV-006).
function classify.activity(prev, cur)
  if prev == nil or cur == nil then return "unknown" end
  if prev.recipe ~= cur.recipe then return "unknown" end          -- recipe changed (§8)
  local pf_prev, pf_cur = prev.products_finished, cur.products_finished
  if pf_prev == nil or pf_cur == nil then return "unknown" end
  if pf_cur < pf_prev then return "unknown" end                    -- counter discontinuity
  if pf_cur > pf_prev then return "progressing" end                -- >=1 craft completed
  local cp_prev, cp_cur = prev.crafting_progress, cur.crafting_progress
  if cp_prev == nil or cp_cur == nil then return "unknown" end
  if cp_cur > cp_prev then return "progressing" end
  if cp_cur < cp_prev then return "unknown" end                    -- reset without completion
  return "not_progressing"
end

--- Headline from measured activity + supported cause (ADR 0007 §17).
--- Returns headline, cause, mapped (mapped=false when the raw status is
--- outside the adapter's table -> unclassified coverage, §15).
function classify.headline(activity, raw_status_name)
  local cause = classify.CAUSE_BY_STATUS[raw_status_name]
  local mapped = cause ~= nil
  if activity == "progressing" then
    -- Progress wins: a constrained-but-progressing machine stays productive
    -- and keeps its condition (e.g. low_power brownout, §12/§18).
    return "productive", (mapped and cause or "unknown"), mapped
  end
  if not mapped then
    return "unclassified", "unknown", false
  end
  if cause == "input_shortage" then return "starved", cause, true end
  if cause == "output_blocked" then return "blocked", cause, true end
  if cause == "energy_unavailable" or cause == "energy_limited"
      or cause == "equipment_unavailable" then
    return "unavailable", cause, true
  end
  if cause == "disabled_control" then return "disabled", cause, true end
  if cause == "configuration" then return "idle_other", cause, true end
  -- cause == "none" (raw `working`) with no measured progress: status and
  -- evidence disagree — visible as idle_other, worth adapter scrutiny (§ table)
  return "idle_other", cause, true
end

--- Full interval classification. Returns a plain record:
--- {activity=..., cause=..., headline=..., raw_status=..., mapped=bool}
---
--- ADR 0007 §24: when activity evidence is missing/untrustworthy the
--- interval is MISSING MEASUREMENT (`coverage_missing`), never silently a
--- classified state — the full-window denominator does not shrink and the
--- gap is visible as coverage (ADR 0010 §12).
function classify.interval(prev_sample, cur_sample, raw_status_name)
  local activity = classify.activity(prev_sample, cur_sample)
  if activity == "unknown" then
    return {
      activity = activity,
      cause = classify.CAUSE_BY_STATUS[raw_status_name] or "unknown",
      headline = "coverage_missing",
      raw_status = raw_status_name,
      mapped = classify.CAUSE_BY_STATUS[raw_status_name] ~= nil,
    }
  end
  local headline, cause, mapped = classify.headline(activity, raw_status_name)
  return {
    activity = activity,
    cause = cause,
    headline = headline,
    raw_status = raw_status_name,
    mapped = mapped,
  }
end

return classify
