--[[
NOTE: This file is only used for type hinting and developer experience. (for intellisense, etc)
      Please do not modify unless its absolutely necessary.
]]


--- @diagnostic disable: lowercase-global

--- @type string
--- @doc Incoming Request Body
--- @global
body = "\x89PNG\r\n\x1a\n"

--- @type table<string, string>
--- @doc Incoming Request Headers
--- @global
headers = {}

--- @type table<string, string>
--- @global Incoming Request Query Parameters
--- @global
params = {}

--- @type table<string, string>
--- @global Flow environment variables
--- @global
env = {}
