"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Proxy = void 0;
var net_1 = __importDefault(require("net"));
var Proxy = /** @class */ (function () {
    function Proxy(IP, PORT) {
        this.IP = IP;
        this.PORT = PORT;
        this.Server = net_1.default.createServer();
    }
    Proxy.prototype.Run = function () {
        this.Server.on("connection", function (soc) {
            soc.on("data", function (DATA) {
                var data = DATA.toString("utf-8");
                var RequestData = data.split("\n\r");
                RequestData.forEach(function (value) {
                    console.log(value, " \n");
                });
            });
        });
        this.Start();
    };
    Proxy.prototype.Start = function () {
        var _this = this;
        this.Server.listen(this.PORT, this.IP, function () {
            console.log("Proxy Server runinng on IP: ".concat(_this.IP, " PORT: ").concat(_this.PORT));
        });
    };
    return Proxy;
}());
exports.Proxy = Proxy;
