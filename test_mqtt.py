#!/usr/bin/env python3
import mqtt as m
import time

def main():
    client = m.connect()
    counter = 0
    while True:
        m.write(client, counter)
        counter += 1
        time.sleep(1)

if __name__ == "__main__":
    main()
