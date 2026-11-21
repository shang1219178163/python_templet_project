class Boom:
    def start(self):
        print("boom start")


class Game:
    def start(self):
        print("Game Game")


def start(something):
    something.start()


start(Boom())
start(Game())
