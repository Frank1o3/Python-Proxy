"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var Proxy_1 = require("./Proxy");
var Server = new Proxy_1.Proxy("10.0.0.31", 8080);
Server.Run();
