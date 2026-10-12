-- Builds .aseprite files from the text dumps written by make_all.py.
--   mode=frames : one frame per tile/sprite frame, frame tags per group. Tiles are 8x16 on an
--                 opaque background; sprite dumps give 'size w h' and 'transparent' (pen 0 = mask)
--   mode=tilemap: one tileset + tilemap layer (paint levels with Aseprite's tilemap mode)
-- Usage: aseprite -b --script-param in=dump.txt --script-param out=x.aseprite
--                    --script-param mode=frames --script make_aseprite.lua

local inpath, outpath = app.params["in"], app.params["out"]
local mode = app.params["mode"] or "frames"

local pal, tags, tiles, map = {}, {}, {}, {}
local mapW, mapH, name = 0, 0, "tiles"
local fw, fh, transparent = 8, 16, false
for line in io.lines(inpath) do
  local kind, rest = line:match("^(%S+)%s*(.*)$")
  if kind == "name" then
    name = rest
  elseif kind == "size" then
    fw, fh = rest:match("(%d+)%s+(%d+)")
    fw, fh = tonumber(fw), tonumber(fh)
  elseif kind == "transparent" then
    transparent = true
  elseif kind == "pal" then
    for hex in rest:gmatch("%x%x%x%x%x%x") do pal[#pal + 1] = hex end
  elseif kind == "tag" then
    local n, a, b, dir = rest:match("(%S+)%s+(%d+)%s+(%d+)%s*(%a*)")
    tags[#tags + 1] = { n, tonumber(a), tonumber(b), dir }
  elseif kind == "tile" then
    local n, hex, ms = rest:match("(%S+)%s+(%x+)%s*(%d*)")
    tiles[#tiles + 1] = { n, hex, tonumber(ms) }
  elseif kind == "map" then
    mapW, mapH = rest:match("(%d+)%s+(%d+)")
    mapW, mapH = tonumber(mapW), tonumber(mapH)
  elseif kind == "row" then
    local r = {}
    for v in rest:gmatch("%d+") do r[#r + 1] = tonumber(v) end
    map[#map + 1] = r
  end
end

local function tile_image(hex)
  local img = Image(fw, fh, ColorMode.INDEXED)
  for y = 0, fh - 1 do
    for x = 0, fw - 1 do
      local k = y * fw + x + 1
      img:drawPixel(x, y, tonumber(hex:sub(k, k), 16))
    end
  end
  return img
end

local function set_palette(spr)
  local p = Palette(#pal)
  for i, hex in ipairs(pal) do
    p:setColor(i - 1, Color { r = tonumber(hex:sub(1, 2), 16), g = tonumber(hex:sub(3, 4), 16),
                              b = tonumber(hex:sub(5, 6), 16), a = 255 })
  end
  spr:setPalette(p)
end

if mode == "frames" then
  local spr = Sprite(fw, fh, ColorMode.INDEXED)
  app.activeSprite = spr
  set_palette(spr)
  spr.pixelRatio = Size(2, 1)
  spr.gridBounds = Rectangle(0, 0, fw, fh)
  if transparent then
    spr.transparentColor = 0                  -- sprites: pen 0 is the mask
  else
    app.command.BackgroundFromLayer()         -- tiles: pen 0 is black, not transparent
  end
  local layer = spr.layers[1]
  layer.name = name
  for i = 2, #tiles do spr:newEmptyFrame() end
  for i, t in ipairs(tiles) do
    local cel = spr:newCel(layer, i, tile_image(t[2]), Point(0, 0))
    cel.data = t[1]                           -- tile/frame name in the cel user data
    if t[3] then spr.frames[i].duration = t[3] / 1000 end
  end
  for _, t in ipairs(tags) do
    local tag = spr:newTag(t[2] + 1, t[3] + 1)
    tag.name = t[1]
    if t[4] == "pingpong" then tag.aniDir = AniDir.PING_PONG end
  end
  spr:saveAs(outpath)
else
  local spr = Sprite(mapW * 8, mapH * 16, ColorMode.INDEXED)
  app.activeSprite = spr
  set_palette(spr)
  spr.pixelRatio = Size(2, 1)
  spr.gridBounds = Rectangle(0, 0, 8, 16)
  app.command.NewLayer { name = name, tilemap = true }
  local layer = app.activeLayer
  local ts = layer.tileset
  ts.name = name
  for i, t in ipairs(tiles) do
    local tile = spr:newTile(ts)
    tile.image = tile_image(t[2])
    tile.data = t[1]
  end
  local img = Image(mapW, mapH, ColorMode.TILEMAP)
  for y = 1, mapH do
    for x = 1, mapW do
      img:drawPixel(x - 1, y - 1, map[y][x] + 1)   -- tile 0 of a tileset is "empty"
    end
  end
  spr:newCel(layer, 1, img, Point(0, 0))
  -- drop the default empty layer
  for _, l in ipairs(spr.layers) do
    if not l.isTilemap then spr:deleteLayer(l) break end
  end
  spr:saveAs(outpath)
end
