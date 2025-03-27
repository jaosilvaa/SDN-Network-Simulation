from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpidToStr
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet.ethernet import ethernet

log = core.getLogger()

class NetworkManager(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        self.mac_to_port = {}
        self.blocked_ports = set()
        self.switch_id = connection.dpid
        log.info(f"Switch {dpidToStr(self.switch_id)} conectado ao controlador")

    def _process_packet(self, event):
        packet = event.parsed
        if not packet.parsed:
            log.warning("Ignorando pacote incompleto")
            return
        
        packet_in = event.ofp
        in_port = event.port
        
        log.debug(f"Pacote recebido no switch {dpidToStr(self.switch_id)} - Origem: {packet.src}, Destino: {packet.dst}, Porta: {in_port}")
        
        if packet.src not in self.mac_to_port:
            log.debug(f"Aprendendo que {packet.src} está na porta {in_port} do switch {dpidToStr(self.switch_id)}")
        self.mac_to_port[packet.src] = in_port
        
        if packet.src in self.mac_to_port and self.mac_to_port[packet.src] != in_port and in_port not in self.blocked_ports:
            log.warning(f"Possível loop detectado no switch {dpidToStr(self.switch_id)} - MAC {packet.src} visto na porta {in_port}, mas já aprendido na porta {self.mac_to_port[packet.src]}")
            self.mac_to_port[packet.src] = in_port
        
        if packet.dst.is_broadcast:
            log.debug(f"Broadcast do switch {dpidToStr(self.switch_id)} - inundando todas as portas, exceto a porta de entrada {in_port}")
            self._flood(event, in_port)
            return
        
        if packet.dst in self.mac_to_port:
            out_port = self.mac_to_port[packet.dst]
            
            if out_port == in_port:
                log.debug(f"Porta de saída ({out_port}) é a mesma que a de entrada ({in_port}), ignorando")
                return
            
            if out_port in self.blocked_ports:
                log.debug(f"Porta de saída {out_port} está bloqueada, inundando")
                self._flood(event, in_port)
                return
            
            self._setup_flow(event, out_port)
            self._forward_packet(event, out_port)
        else:
            log.debug(f"MAC de destino {packet.dst} desconhecido, inundando")
            self._flood(event, in_port)
    
    def _setup_flow(self, event, out_port):
        packet = event.parsed
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.idle_timeout = 20
        msg.hard_timeout = 40
        msg.actions.append(of.ofp_action_output(port=out_port))
        log.debug(f"Instalando regra no switch {dpidToStr(self.switch_id)}: {packet.src} -> {packet.dst} via porta {out_port}")
        self.connection.send(msg)
    
    def _forward_packet(self, event, out_port):
        packet_in = event.ofp
        msg = of.ofp_packet_out()
        msg.data = packet_in
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.in_port = event.port
        log.debug(f"Enviando pacote para a porta {out_port} no switch {dpidToStr(self.switch_id)}")
        self.connection.send(msg)
    
    def _flood(self, event, in_port):
        packet_in = event.ofp
        msg = of.ofp_packet_out()
        msg.data = packet_in
        
        for port_no in [p for p in self.connection.ports if p != in_port and p not in self.blocked_ports]:
            if port_no < of.OFPP_MAX:
                msg.actions.append(of.ofp_action_output(port=port_no))
        
        msg.in_port = in_port
        log.debug(f"Inundando pacote do switch {dpidToStr(self.switch_id)}")
        self.connection.send(msg)

    def disable_port(self, port):
        if port not in self.blocked_ports:
            self.blocked_ports.add(port)
            log.info(f"Porta {port} bloqueada no switch {dpidToStr(self.switch_id)} para evitar loops")
            
            msg = of.ofp_flow_mod()
            msg.match.in_port = port
            self.connection.send(msg)

    def enable_port(self, port):
        if port in self.blocked_ports:
            self.blocked_ports.remove(port)
            log.info(f"Porta {port} desbloqueada no switch {dpidToStr(self.switch_id)}")
            
            msg = of.ofp_flow_mod()
            msg.match.in_port = port
            msg.command = of.OFPFC_DELETE
            self.connection.send(msg)

    _handle_PacketIn = _process_packet

def launch():
    def start_controller(event):
        log.debug(f"Controlando switch {dpidToStr(event.connection.dpid)}")
        NetworkManager(event.connection)
    
    core.openflow.addListenerByName("ConnectionUp", start_controller)
    
    log.info("Controlador SDN para a Questão 02 iniciado!")