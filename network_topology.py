from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
import os

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
    h3 = net.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)
    h4 = net.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None)
    h5 = net.addHost('h5', cls=Host, ip='10.0.0.5', defaultRoute=None)
    h6 = net.addHost('h6', cls=Host, ip='10.0.0.6', defaultRoute=None)
    h7 = net.addHost('h7', cls=Host, ip='10.0.0.7', defaultRoute=None)

    info( '*** Add links\n')

    h1s1 = {'bw':100,'loss':0.5,'max_queue_size':100}
    net.addLink(h1, s1, cls=TCLink , **h1s1)
    h2s1 = {'bw':100,'loss':0.5,'max_queue_size':100}
    net.addLink(h2, s1, cls=TCLink , **h2s1)
    h3s1 = {'bw':100,'loss':0.5,'max_queue_size':100}
    net.addLink(h3, s1, cls=TCLink , **h3s1)
    s5h6 = {'bw':100,'loss':0.5,'max_queue_size':100}
    net.addLink(s5, h6, cls=TCLink , **s5h6)
    s4h7 = {'bw':100,'loss':0.5,'max_queue_size':100}
    net.addLink(s4, h7, cls=TCLink , **s4h7)
    s2h4 = {'bw':100,'loss':0.5,'max_queue_size':100}
    net.addLink(s2, h4, cls=TCLink , **s2h4)
    s2h5 = {'bw':100,'loss':0.5,'max_queue_size':100}
    net.addLink(s2, h5, cls=TCLink , **s2h5)

    s1s2 = {'bw':100,'delay':'1ms','loss':1, 'max_queue_size':100}
    net.addLink(s1, s2, cls=TCLink , **s1s2)
    s2s5 = {'bw':100,'delay':'1ms','loss':1, 'max_queue_size':100}
    net.addLink(s2, s5, cls=TCLink , **s2s5)
    s4s5 = {'bw':100,'delay':'1ms','loss':1, 'max_queue_size':100}
    net.addLink(s4, s5, cls=TCLink , **s4s5)
    s4s1 = {'bw':100,'delay':'1ms','loss':1, 'max_queue_size':100}
    net.addLink(s4, s1, cls=TCLink , **s4s1)
    s1s3 = {'bw':100,'delay':'1ms','loss':1, 'max_queue_size':100}
    net.addLink(s1, s3, cls=TCLink , **s1s3)
    s3s5 = {'bw':100,'delay':'1ms','loss':1, 'max_queue_size':100}
    net.addLink(s3, s5, cls=TCLink , **s3s5)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])
    net.get('s5').start([c0])

    info( '*** Post configure switches and hosts\n')

    # Ativar STP 
    switch_list = [s1, s2, s3, s4, s5] 
    for switch in switch_list:
        info('* Active STP on %s\n' % switch.name)
        os.system(f"ovs-vsctl set bridge {switch.name} stp_enable=true")
        
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()