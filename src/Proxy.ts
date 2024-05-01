import net from 'net';
import { isDataView } from 'util/types';

export class Proxy {
    private IP:string;
    private PORT:number;
    private Server:net.Server;

    constructor (IP:string,PORT:number) {
        this.IP = IP;
        this.PORT = PORT;
        this.Server = net.createServer();
    }

    public Run() {
        this.Server.on("connection", (soc:net.Socket) => {
            soc.on("data", (DATA:Buffer) => {
                const data = DATA.toString("utf-8");
                const RequestData = data.split("\n\r");
                RequestData.forEach(value => {
                    console.log(value," \n");
                });
            });
        });
        this.Start()
    }

    
    private Start() {
        this.Server.listen(this.PORT,this.IP,() => {
            console.log(`Proxy Server runinng on IP: ${this.IP} PORT: ${this.PORT}`);
        });
    }
}