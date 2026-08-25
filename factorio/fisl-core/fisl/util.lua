-- Small pure helpers: CRC32 for config transfer verification (ADR 0015 §6)
-- and runtime API compatibility shims whose exact behavior is subject to the
-- RUNTIME_VALIDATION.md gate.

local util = {}

-- CRC-32 (IEEE 802.3, same polynomial/reflection as Python zlib.crc32),
-- implemented with bit32 which is available in Factorio's Lua 5.2 runtime.
local crc_table
local function build_crc_table()
  crc_table = {}
  for i = 0, 255 do
    local crc = i
    for _ = 1, 8 do
      if bit32.band(crc, 1) == 1 then
        crc = bit32.bxor(bit32.rshift(crc, 1), 0xEDB88320)
      else
        crc = bit32.rshift(crc, 1)
      end
    end
    crc_table[i] = crc
  end
end

function util.crc32(text)
  if not crc_table then build_crc_table() end
  local crc = 0xFFFFFFFF
  for i = 1, #text do
    local byte = string.byte(text, i)
    crc = bit32.bxor(bit32.rshift(crc, 8), crc_table[bit32.band(bit32.bxor(crc, byte), 0xFF)])
  end
  return bit32.bxor(crc, 0xFFFFFFFF)
end

-- JSON encode/decode via the Factorio helpers API (2.0). RV-008 evidence
-- should confirm exact availability; `game` fallbacks cover late-1.1 names.
function util.json_encode(tbl)
  if helpers and helpers.table_to_json then return helpers.table_to_json(tbl) end
  return game.table_to_json(tbl)
end

function util.json_decode(text)
  if helpers and helpers.json_to_table then return helpers.json_to_table(text) end
  return game.json_to_table(text)
end

-- Decode base64 + inflate (controller sends deflated+base64 config chunks).
function util.decode_payload(text)
  if helpers and helpers.decode_string then return helpers.decode_string(text) end
  return game.decode_string(text)
end

function util.write_file(path, text, append)
  if helpers and helpers.write_file then
    helpers.write_file(path, text, append)
  else
    game.write_file(path, text, append)
  end
end

-- Inventory define compatibility: 2.0 renamed assembling-machine inventories.
function util.crafter_input_define()
  return defines.inventory.crafter_input or defines.inventory.assembling_machine_input
end

function util.crafter_output_define()
  return defines.inventory.crafter_output or defines.inventory.assembling_machine_output
end

-- Item counting across 1.1 (dict) / 2.0 (array of {name,count,quality})
-- get_contents() shapes; RV-004 confirms which one the pinned runtime uses.
function util.contents_count(contents, item_name)
  if contents == nil then return 0 end
  local total = 0
  local dict_value = contents[item_name]
  if type(dict_value) == "number" then
    total = total + dict_value
  end
  for index, entry in pairs(contents) do
    if type(entry) == "table" and entry.name == item_name then
      total = total + (entry.count or 0)
    end
  end
  return total
end

return util
