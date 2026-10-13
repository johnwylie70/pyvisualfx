from pyctures import *
from pyvisualfx import *

t = 0
frames = 0
mirror("four")
soft = blur(6)
turned = hue(90)
shine = glow(0.5, radius=20)
shine.off()

def update(dt):
    global t, frames
    t += dt
    frames += 1
    js.pyClock = [t, frames]
    if frames == 5:
        soft.radius = 10
        turned.shift += 30

def draw():
    background("black")
    circle(120, 90, 40, "gold")
    rect(40, 150, 90, 50, "deepskyblue")
    line(0, 0, 200, 120, "tomato", 6)
