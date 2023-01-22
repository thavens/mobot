from pygame import joystick, time
import threading
import math
import options

def clamp(input: float) -> int:
    return int(input) if abs(input) < 1000 else int(math.copysign(1000, input))

def deadband(input: float) -> float:
    if input < options.JOY_DEADBAND and input > -options.JOY_DEADBAND:
        return 0
    else:
        return (input - math.copysign(options.JOY_DEADBAND, input)) / (1 - options.JOY_DEADBAND)

class Controller(threading.Thread):
    def __init__(self, id, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.joy = joystick.Joystick(id)
        self.values = [0] * self.joy.get_numaxes()
        self.hat = (0, 0)
    
    def run(self):
        clock = time.Clock()
        while 1:
            self.joy.init()
            self.values = [self.joy.get_axis(i) for i in range(self.joy.get_numaxes())]
            self.values = [deadband(i) for i in self.values]
            self.values = [clamp(i * 1000 * options.SPEEDRATIO) for i in self.values]
            self.values[1] = -self.values[1]
            self.hat = self.joy.get_hat(0)
            self.joy.quit()
            clock.tick(60)
    
    def bytes(self):
        return (i.to_bytes(2, 'little', signed=True) for i in self)
    
    def __len__(self):
        return len(self.values) + len(self.hat)

    def __getitem__(self, idx):
        return self.values[idx] if idx < 4 else self.hat[idx - 4]

def get_controller():
    joy_id = 0
    joystick.init()
    if joystick.get_count() > 1:
        for i in range(joystick.get_count()):
            print(i, joystick.Joystick(i).get_name())
        joy_id = int(input('There are multiple joysticks which would you like to use? '))

    controller = Controller(joy_id, daemon=True)
    controller.start()
    return controller

if __name__ == '__main__':
    controller = get_controller()
    clock = time.Clock()
    
    while(1):
        print(', '.join(f'{i}'.rjust(6) for i in controller), end='\r')
        clock.tick(120)



