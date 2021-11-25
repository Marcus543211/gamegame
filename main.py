import logging

import pygame

import network


def main():
    logging.basicConfig(level=logging.INFO)

    should_host = input('Host [y/n]? ')

    if 'y' in should_host.lower():
        server = network.EchoServer('0.0.0.0')

        print(f'Connect on address: {network.get_local_ip()}:{server.port}')

        address = ('127.0.0.1', server.port)
    else:
        server = None

        address = input('Please enter the adress with port to connect to: ')
        address = tuple(address.strip().split(':'))

    client = network.Client(*address)

    pygame.init()

    pygame.display.set_caption('CannedCritters')
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    while True:
        clock.tick(120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.close()
                if server:
                    server.close()
                return

            if event.type == pygame.KEYDOWN:
                client.send(event.key)

        if server:
            server.step()

        while packet := client.recive():
            print(packet)

        screen.fill(pygame.Color('white'))
        pygame.display.flip()


if __name__ == "__main__":
    main()
