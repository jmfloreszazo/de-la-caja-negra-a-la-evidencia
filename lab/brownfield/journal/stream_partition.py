#!/usr/bin/env python3
"""Opaque stream suppression on live sockets; not a kernel packet-loss emulator."""
import select
import socket
import socketserver
import threading
import time


class StreamPartition:
    def __init__(self, listen_port=55440, backend_port=55441):
        self.lock=threading.Lock()
        self.mode='FORWARD'
        self.streams=set()
        self.events=[]
        self.counts={'CLIENT_TO_SERVER':0,'SERVER_TO_CLIENT':0}
        self.forwarded={'CLIENT_TO_SERVER':0,'SERVER_TO_CLIENT':0}
        self.accepted=0
        owner=self
        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                front=self.request
                back=None
                try:
                    back=socket.create_connection(('127.0.0.1',backend_port),timeout=3)
                    back.settimeout(None)
                    with owner.lock:
                        owner.streams.update((front,back));owner.accepted+=1
                    while True:
                        ready,_,_=select.select([front,back],[],[],.05)
                        for source in ready:
                            data=source.recv(65536)
                            if not data:return
                            direction='CLIENT_TO_SERVER' if source is front else 'SERVER_TO_CLIENT'
                            with owner.lock:
                                if owner.mode==direction:
                                    owner.counts[direction]+=len(data)
                                    continue
                                owner.forwarded[direction]+=len(data)
                            (back if source is front else front).sendall(data)
                except (OSError,ValueError):
                    pass
                finally:
                    with owner.lock:
                        owner.streams.discard(front)
                        if back is not None:owner.streams.discard(back)
                    if back is not None:back.close()
        class Server(socketserver.ThreadingTCPServer):
            allow_reuse_address=True
            daemon_threads=True
        self.server=Server(('127.0.0.1',listen_port),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)

    def __enter__(self):
        self.thread.start();return self

    def snapshot(self):
        with self.lock:
            return {'mode':self.mode,'droppedBytes':dict(self.counts),'forwardedBytes':dict(self.forwarded),
                    'activeConnections':len(self.streams)//2,'acceptedConnections':self.accepted,
                    'monotonicNs':time.monotonic_ns()}

    def suppress(self,direction):
        if direction not in ('CLIENT_TO_SERVER','SERVER_TO_CLIENT'):raise ValueError('Unknown direction')
        with self.lock:
            if self.mode!='FORWARD':raise ValueError('Reset required before another fault')
            self.mode=direction;self.counts={k:0 for k in self.counts};self.forwarded={k:0 for k in self.forwarded}
        event={'event':'SILENT_STREAM_SUPPRESSION',**self.snapshot()}
        self.events.append(event);return event

    def reset(self):
        # Dropped protocol bytes cannot safely be restored to an existing stream.
        # Close every test connection explicitly before allowing fresh sessions.
        with self.lock:
            streams=list(self.streams)
            for stream in streams:
                try:stream.shutdown(socket.SHUT_RDWR)
                except OSError:pass
                stream.close()
            self.mode='FORWARD'
        event={'event':'CONTROLLED_SOCKET_RESET','closedConnections':len(streams)//2,
               'monotonicNs':time.monotonic_ns()}
        self.events.append(event);return event

    def __exit__(self,*exc):
        self.reset();self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)
