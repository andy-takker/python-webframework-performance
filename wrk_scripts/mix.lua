math.randomseed(os.time())
request = function()
  local id = math.random(1, 100000)
  if math.random() < 0.7 then
    return wrk.format("GET", "/mix?id=" .. id)
  elseif math.random() < 0.5 then
    return wrk.format("GET", "/cache/get?key=k" .. id)
  else
    return wrk.format("GET", "/cache/set?key=k" .. id .. "&value=v" .. id)
  end
end
