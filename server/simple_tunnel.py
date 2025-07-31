#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple TCP tunnel/proxy for UPass Server
Forwards connections from 0.0.0.0:PORT to 127.0.0.1:PORT
For testing purposes or simple network setups
"""

import socket
import threading
import argparse
import sys
import signal

class SimpleTunnel:
    def __init__(self, listen_port, target_port):
        self.listen_port = listen_port
        self.target_port = target_port
        self.running = True
        self.threads = []
        
    def handle_client(self, client_socket, client_addr):
        """Handle incoming client connection"""
        try:
            # Connect to localhost server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect(('127.0.0.1', self.target_port))
            
            # Create threads for bidirectional forwarding
            client_to_server = threading.Thread(
                target=self.forward_data,
                args=(client_socket, server_socket, f"{client_addr} -> localhost")
            )
            server_to_client = threading.Thread(
                target=self.forward_data,
                args=(server_socket, client_socket, f"localhost -> {client_addr}")
            )
            
            client_to_server.daemon = True
            server_to_client.daemon = True
            
            client_to_server.start()
            server_to_client.start()
            
            # Wait for threads to finish
            client_to_server.join()
            server_to_client.join()
            
        except Exception as e:
            print(f"Error handling client {client_addr}: {e}")
        finally:
            client_socket.close()
            if 'server_socket' in locals():
                server_socket.close()
    
    def forward_data(self, source, destination, direction):
        """Forward data between sockets"""
        try:
            while self.running:
                data = source.recv(4096)
                if not data:
                    break
                destination.sendall(data)
        except:
            pass
        finally:
            source.close()
            destination.close()
    
    def start(self):
        """Start the tunnel server"""
        # Create listening socket
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            listen_socket.bind(('0.0.0.0', self.listen_port))
            listen_socket.listen(5)
            print(f"[TUNNEL] Simple tunnel started")
            print(f"         Forwarding: 0.0.0.0:{self.listen_port} -> 127.0.0.1:{self.target_port}")
            print(f"         External connections can now reach your UPass server")
            print(f"         Press Ctrl+C to stop")
            print()
            
            while self.running:
                try:
                    client_socket, client_addr = listen_socket.accept()
                    print(f"[+] New connection from {client_addr[0]}:{client_addr[1]}")
                    
                    # Handle client in new thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    self.threads.append(client_thread)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    if self.running:
                        print(f"Error accepting connection: {e}")
                        
        except Exception as e:
            print(f"Failed to start tunnel: {e}")
            sys.exit(1)
        finally:
            self.running = False
            listen_socket.close()
            print("\n[TUNNEL] Tunnel stopped")
    
    def stop(self):
        """Stop the tunnel"""
        self.running = False

def main():
    parser = argparse.ArgumentParser(
        description='Simple TCP tunnel for UPass Server - Forwards external port to localhost'
    )
    parser.add_argument('--port', '-p', type=int, default=8080,
                       help='External port to listen on (default: 8080)')
    parser.add_argument('--target-port', '-t', type=int, default=8000,
                       help='Target localhost port (default: 8000)')
    
    args = parser.parse_args()
    
    # Check if localhost server is running
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_socket.connect(('127.0.0.1', args.target_port))
        test_socket.close()
        print(f"[OK] Found UPass server running on localhost:{args.target_port}")
    except:
        print(f"[WARN] No server found on localhost:{args.target_port}")
        print(f"       Make sure to run: python3 run.py --port {args.target_port}")
        print()
    
    # Create and start tunnel
    tunnel = SimpleTunnel(args.port, args.target_port)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        tunnel.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        tunnel.start()
    except KeyboardInterrupt:
        tunnel.stop()

if __name__ == '__main__':
    main()