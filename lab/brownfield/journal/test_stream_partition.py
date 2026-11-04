"""Socket and observation-oracle controls; no vendor or SQL acceptance claim."""
import copy
import socket
import socketserver
import threading
import time
import unittest
from stream_partition import StreamPartition
from partition_oracle import evaluate


class PartitionTests(unittest.TestCase):
    def test_each_direction_suppresses_bytes_without_closing_live_stream(self):
        for mode in ('CLIENT_TO_SERVER','SERVER_TO_CLIENT'):
            class Echo(socketserver.BaseRequestHandler):
                def handle(self):
                    try:
                        while data:=self.request.recv(64):self.request.sendall(data)
                    except OSError:pass
            class Server(socketserver.ThreadingTCPServer):daemon_threads=True
            with Server(('127.0.0.1',0),Echo) as backend:
                thread=threading.Thread(target=backend.serve_forever,daemon=True);thread.start()
                try:
                    with StreamPartition(0,backend.server_address[1]) as gate:
                        with socket.create_connection(gate.server.server_address,timeout=2) as client:
                            client.sendall(b'healthy');self.assertEqual(client.recv(64),b'healthy')
                            gate.suppress(mode);client.sendall(b'probe');client.settimeout(.2)
                            with self.assertRaises(socket.timeout):client.recv(64)
                            state=gate.snapshot();self.assertGreater(state['droppedBytes'][mode],0)
                            reverse='SERVER_TO_CLIENT' if mode=='CLIENT_TO_SERVER' else 'CLIENT_TO_SERVER'
                            self.assertEqual(state['droppedBytes'][reverse],0);self.assertEqual(state['activeConnections'],1)
                            gate.reset()
                        with socket.create_connection(gate.server.server_address,timeout=2) as fresh:
                            fresh.sendall(b'restored');self.assertEqual(fresh.recv(64),b'restored')
                finally:backend.shutdown();thread.join(timeout=3)

    def test_oracle_rejects_false_absence_and_unobserved_transport_claim(self):
        case={'writer':'legacy','direction':'CLIENT_TO_SERVER','beforeCounts':[0,0,0],
              'silentObservation':{'droppedBytes':{'CLIENT_TO_SERVER':10,'SERVER_TO_CLIENT':0},'activeConnections':3},
              'controllerPidsDuringFault':[1], 'blockedReconnectExit':1,'switchAttemptExit':1,
              'controllerAuthorityUnchanged':True,'financialCountsWhileSuppressed':[1,2,1],
              'finalCounts':[1,2,1],'reconciledStatus':'COMMITTED','replayStatus':'DUPLICATE_COMMITTED',
              'sourceOracle':{'ok':True},'targetOracle':{'ok':True},'journalAuditPassed':True,
              'recoveryIntervention':'CONTROLLED_SOCKET_RESET','probeExitedDuringFault':False,
              'probeQueryObservedAtServer':False}
        self.assertEqual(evaluate(case),[])
        for name,change in [('false absence',lambda c:c.update(financialCountsWhileSuppressed=[0,0,0])),
                            ('no fault bytes',lambda c:c['silentObservation']['droppedBytes'].update(CLIENT_TO_SERVER=0)),
                            ('lost sessions',lambda c:c.update(controllerPidsDuringFault=[])),
                            ('false automatic recovery',lambda c:c.update(recoveryIntervention='AUTOMATIC'))]:
            mutant=copy.deepcopy(case);change(mutant);self.assertTrue(evaluate(mutant),name)

if __name__=='__main__':unittest.main()
