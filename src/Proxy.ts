import net from 'net';

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
            soc.on("connect", (data:Buffer) => {
                console.log(data);
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