-- Φτιάχνει .aseprite spritemaps από το aseprite_dump.txt του make_sprites.py.
--
--   aseprite -b --script-param in=aseprite_dump.txt --script-param out=DIR \
--            --script make_aseprite.lua
--
-- Μορφή dump:  pal RRGGBB x16 / group <όνομα> <w> <h> / frame <όνομα> <hex pens>
--
-- Ένα αρχείο ανά ομάδα, ένα frame ανά sprite, ένα tag ανά frame (με το όνομά
-- του). Indexed, pixelRatio 2:1, pen 0 = διαφανές (τα sprites έχουν μάσκα).

local inpath = INPATH or app.params["in"]
local outdir = OUTDIR or app.params["out"]
local prefix = PREFIX or "planetbase_"

local pal, groups = {}, {}
local cur = nil
for line in io.lines(inpath) do
  local kind, rest = line:match("^(%S+)%s*(.*)$")
  if kind == "pal" then
    for hex in rest:gmatch("%x%x%x%x%x%x") do pal[#pal + 1] = hex end
  elseif kind == "group" then
    local n, w, h = rest:match("(%S+)%s+(%d+)%s+(%d+)")
    cur = { name = n, w = tonumber(w), h = tonumber(h), frames = {} }
    groups[#groups + 1] = cur
  elseif kind == "frame" then
    local n, hex = rest:match("(%S+)%s+(%x+)")
    cur.frames[#cur.frames + 1] = { name = n, hex = hex }
  end
end

local function palette()
  local p = Palette(#pal)
  for i, hex in ipairs(pal) do
    p:setColor(i - 1, Color {
      r = tonumber(hex:sub(1, 2), 16),
      g = tonumber(hex:sub(3, 4), 16),
      b = tonumber(hex:sub(5, 6), 16), a = 255 })
  end
  return p
end

local made = 0
for _, g in ipairs(groups) do
  local spr = Sprite(g.w, g.h, ColorMode.INDEXED)
  app.activeSprite = spr
  spr:setPalette(palette())
  spr.pixelRatio = Size(2, 1)          -- Mode 0: κάθε pixel διπλάσιο σε πλάτος
  spr.gridBounds = Rectangle(0, 0, g.w, g.h)
  spr.transparentColor = 0             -- pen 0 = διαφανές

  local layer = spr.layers[1]
  layer.name = g.name
  while #spr.frames < #g.frames do spr:newEmptyFrame() end

  for i, f in ipairs(g.frames) do
    local img = Image(g.w, g.h, ColorMode.INDEXED)
    for y = 0, g.h - 1 do
      for x = 0, g.w - 1 do
        local k = y * g.w + x + 1
        img:drawPixel(x, y, tonumber(f.hex:sub(k, k), 16))
      end
    end
    spr:newCel(layer, i, img, Point(0, 0))
    spr.frames[i].duration = 0.1
    local tag = spr:newTag(i, i)
    tag.name = f.name
  end

  local base = outdir .. "/" .. prefix .. g.name .. "_cpc_mode0"
  spr:saveAs(base .. ".aseprite")
  app.command.ExportSpriteSheet {
    ui = false, askOverwrite = false, type = SpriteSheetType.ROWS,
    textureFilename = base .. "_sheet.png",
    dataFilename = base .. "_sheet.json",
    dataFormat = SpriteSheetDataFormat.JSON_ARRAY,
    listTags = true, trim = false,
  }
  spr:close()
  made = made + 1
  print(string.format("%-28s %2d frames  %dx%d", g.name, #g.frames, g.w, g.h))
end
print("σύνολο αρχείων: " .. made)
