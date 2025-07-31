#!/usr/bin/env python3
import argparse
from app.server import run_server

def main():
    parser = argparse.ArgumentParser(description='UPass Server - Zero-knowledge password manager')
    parser.add_argument('--port', '-p', type=int, default=8000, 
                       help='Port to run the server on (default: 8000)')
    
    args = parser.parse_args()
    
    run_server(port=args.port)

if __name__ == '__main__':
    main()