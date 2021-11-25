import multiprocessing

import pygame

import network


def main():
    should_host = input('Host [y/n]? ')

    if 'y' in should_host.lower():
        server = network.EchoServer('0.0.0.0')
        address = ('127.0.0.1', server.address[1])

        host = multiprocessing.Process(target=server.serve)
        host.start()
    else:
        host = None

        address = input('Please enter the adress with port to connect to: ')
        address = tuple(address.strip().split(':'))

    client = network.Client(*address)

    message = "Hello world!"
    client.send(message)

    message = client.recive()
    print(message)

    pygame.init()

    pygame.display.set_caption('CannedCritters')
    screen = pygame.display.set_mode((800, 600))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.close()
                if host:
                    host.terminate()

                return

        screen.fill(pygame.Color('white'))
        pygame.display.flip()


if __name__ == "__main__":
    main()
