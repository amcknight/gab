from pykka import ThreadingActor


class Fleet(ThreadingActor):
    num_msgs = 0

    def __init__(self, actor, num):
        super().__init__()
        self.num = num
        self.actors = [actor.start() for _ in range(self.num)]

    def on_receive(self, msg):
        self.num_msgs += 1
        index = self.num_msgs % self.num
        self.actors[index].tell(msg)
