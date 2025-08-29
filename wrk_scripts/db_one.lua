math.randomseed(os.time())
request = function()
  local id = math.random(1, 100000)
  return wrk.format("GET", "/db/one?id=" .. id)
end