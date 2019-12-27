from aoc2019.intcode import IntcodeProgram, ExecutionInterrupt
from dataclasses import dataclass


class NetworkDevice:
    def __init__(self, address, prog):
        self.address = address
        self.inputs = [address]
        self.outputs = []
        self.program = IntcodeProgram(prog, self.inputs, self.outputs)
        self.out_buffer = []
        self.in_buffer = None

    def is_idle(self):
        return len(self.out_buffer) == 0 and self.in_buffer is None

    def tick(self, net_in, net_out):
        result = self.program.execute_until_interrupt()
        if result == ExecutionInterrupt.NEED_INPUT:
            if self.in_buffer is not None:
                # X must have been already sent, just send Y now
                self.inputs.append(self.in_buffer[2])
                self.in_buffer = None
            elif net_in:
                self.in_buffer = net_in.pop(0)
                self.inputs.append(self.in_buffer[1])
            else:
                self.inputs.append(-1)
        if result == ExecutionInterrupt.HAS_OUTPUT:
            self.out_buffer.append(self.outputs.pop(0))
            if len(self.out_buffer) == 3:
                net_out.append(tuple(self.out_buffer))
                self.out_buffer.clear()
        if result == ExecutionInterrupt.HALT:
            return


@dataclass
class Network:
    devices: [NetworkDevice]
    in_queues: dict
    nat_packet: []

    @classmethod
    def create(cls, n):
        program = [int(s) for s in open("day23/input1.txt").read().strip().split(',')]
        devices = [NetworkDevice(address, program) for address in range(n)]
        in_queues = {i: [] for i in range(n)}
        return Network(devices, in_queues, [])

    def is_idle(self):
        return all([len(v) == 0 for k, v in self.in_queues.items()]) and all([d.is_idle() for d in self.devices])

    def run(self):
        last_nat_packet_y = None
        channel = []
        while True:
            for i, device in enumerate(self.devices):
                device.tick(self.in_queues[i], channel)
                if channel:
                    packet = channel.pop(0)
                    print(packet)
                    if packet[0] == 255:
                        self.nat_packet.clear()
                        self.nat_packet.append(packet)
                    else:
                        self.in_queues[packet[0]].append(packet)
            if self.is_idle() and self.nat_packet:
                p = self.nat_packet[0]
                self.in_queues[0].append((0, p[1], p[2]))
                if p[2] == last_nat_packet_y:
                    print(f"NAT packet Y twice in a row = {p[2]}")
                    return
                last_nat_packet_y = p[2]
                self.nat_packet.clear()





network = Network.create(50)
network.run()